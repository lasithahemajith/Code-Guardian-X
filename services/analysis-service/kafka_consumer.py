"""Kafka consumer for analysis-service."""
from __future__ import annotations

import json
import logging
import os
import threading

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from diff_extractor import prepare_analysis_files

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC = "pr.events"
OUTPUT_TOPIC = "code.analysis.ready"
CONSUMER_GROUP = "analysis-service"

_stop_event = threading.Event()


def _make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def process_message(msg_value: dict, producer: KafkaProducer) -> None:
    event = prepare_analysis_files(msg_value, diff_content="")
    key = str(event["pr_id"])
    producer.send(OUTPUT_TOPIC, key=key, value=event)
    producer.flush(timeout=10)
    logger.info("Produced code.analysis.ready for pr_id=%s", event["pr_id"])


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
        logger.info("analysis-service consumer started")

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
    thread = threading.Thread(target=run_consumer, daemon=True, name="analysis-consumer")
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
