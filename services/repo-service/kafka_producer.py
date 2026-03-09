"""Kafka producer for repo-service."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


class KafkaEventProducer:
    def __init__(self):
        self._producer: Optional[KafkaProducer] = None

    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
                acks="all",
            )
        return self._producer

    def produce_event(self, topic: str, key: str, value: dict, retries: int = 3) -> bool:
        for attempt in range(1, retries + 1):
            try:
                producer = self._get_producer()
                future = producer.send(topic, key=key, value=value)
                producer.flush(timeout=10)
                future.get(timeout=10)
                logger.info("Produced event to %s key=%s", topic, key)
                return True
            except KafkaError as exc:
                logger.warning("Kafka error on attempt %d/%d: %s", attempt, retries, exc)
                self._producer = None
                if attempt < retries:
                    time.sleep(min(2 ** attempt, 8))
            except Exception as exc:
                logger.error("Unexpected error producing event: %s", exc)
                break
        return False

    def close(self):
        if self._producer:
            self._producer.close()
            self._producer = None


producer = KafkaEventProducer()
