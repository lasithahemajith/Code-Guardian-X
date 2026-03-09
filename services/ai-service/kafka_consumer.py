"""Kafka consumer for ai-service."""
from __future__ import annotations

import json
import logging
import os
import threading

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from code_analyzer import analyzer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC = "code.analysis.ready"
OUTPUT_TOPIC = "ai.review.completed"
CONSUMER_GROUP = "ai-service"

_stop_event = threading.Event()


def _make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def process_message(msg_value: dict, producer: KafkaProducer) -> None:
    pr_id = msg_value.get("pr_id")
    all_issues: list = []
    for file_entry in msg_value.get("files", []):
        code = file_entry.get("code", "")
        filename = file_entry.get("file", "unknown")
        if code:
            issues = analyzer.analyze(code, filename)
            all_issues.extend(issues)

    result = {"pr_id": pr_id, "issues": all_issues}
    key = str(pr_id)
    producer.send(OUTPUT_TOPIC, key=key, value=result)
    producer.flush(timeout=10)
    logger.info("Produced ai.review.completed for pr_id=%s with %d issues", pr_id, len(all_issues))


def run_consumer() -> None:
    try:
        consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        producer = _make_producer()
        logger.info("ai-service consumer started")

        for msg in consumer:
            if _stop_event.is_set():
                break
            try:
                process_message(msg.value, producer)
            except Exception as exc:
                logger.error("Error processing message: %s", exc)

        consumer.close()
        producer.close()
    except KafkaError as exc:
        logger.warning("Kafka not available: %s", exc)
    except Exception as exc:
        logger.error("Consumer error: %s", exc)


def start_consumer_thread() -> threading.Thread:
    thread = threading.Thread(target=run_consumer, daemon=True, name="ai-consumer")
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
