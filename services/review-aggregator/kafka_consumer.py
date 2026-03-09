"""Kafka consumer for review-aggregator."""
from __future__ import annotations

import json
import logging
import os
import threading

import redis as redis_lib
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from aggregator import aggregate_results

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
AI_TOPIC = "ai.review.completed"
STATIC_TOPIC = "static.analysis.completed"
OUTPUT_TOPIC = "review.finalized"
CONSUMER_GROUP = "review-aggregator"
REDIS_TTL = int(os.getenv("REDIS_RESULT_TTL", "86400"))  # 24 hours default

_stop_event = threading.Event()


def _make_redis() -> redis_lib.Redis:
    return redis_lib.from_url(REDIS_URL, decode_responses=True)


def _make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def process_message(msg_value: dict, topic: str, redis_client, producer: KafkaProducer) -> None:
    pr_id = str(msg_value.get("pr_id"))
    issues = msg_value.get("issues", [])

    if topic == AI_TOPIC:
        redis_client.setex(f"ai:{pr_id}", REDIS_TTL, json.dumps(issues))
    elif topic == STATIC_TOPIC:
        redis_client.setex(f"static:{pr_id}", REDIS_TTL, json.dumps(issues))

    ai_raw = redis_client.get(f"ai:{pr_id}")
    static_raw = redis_client.get(f"static:{pr_id}")

    if ai_raw is not None and static_raw is not None:
        ai_issues = json.loads(ai_raw)
        static_issues = json.loads(static_raw)
        result = aggregate_results(ai_issues, static_issues)
        event = {"pr_id": int(pr_id), **result}
        producer.send(OUTPUT_TOPIC, key=pr_id, value=event)
        producer.flush(timeout=10)
        redis_client.delete(f"ai:{pr_id}", f"static:{pr_id}")
        logger.info("Produced review.finalized for pr_id=%s", pr_id)


def run_consumer() -> None:
    try:
        consumer = KafkaConsumer(
            AI_TOPIC, STATIC_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        redis_client = _make_redis()
        producer = _make_producer()
        logger.info("review-aggregator consumer started")

        for msg in consumer:
            if _stop_event.is_set():
                break
            try:
                process_message(msg.value, msg.topic, redis_client, producer)
            except Exception as exc:
                logger.error("Error processing message: %s", exc)

        consumer.close()
        producer.close()
    except KafkaError as exc:
        logger.warning("Kafka not available: %s", exc)
    except Exception as exc:
        logger.error("Consumer error: %s", exc)


def start_consumer_thread() -> threading.Thread:
    thread = threading.Thread(target=run_consumer, daemon=True, name="aggregator-consumer")
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
