"""Kafka consumer for notification-service."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from notifiers import GitHubNotifier, SlackNotifier

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC = "review.finalized"
CONSUMER_GROUP = "notification-service"

_stop_event = threading.Event()


async def _send_notifications(review_data: dict) -> None:
    github = GitHubNotifier()
    slack = SlackNotifier()

    await slack.send_message(review_data)

    repo = review_data.get("repo", "")
    pr_id = review_data.get("pr_id")
    if repo and pr_id:
        await github.post_pr_comment(repo, int(pr_id), review_data)


def process_message(msg_value: dict) -> None:
    """Process a single notification message (used in tests and consumer)."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_send_notifications(msg_value))
    finally:
        loop.close()


def run_consumer() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        logger.info("notification-service consumer started")

        for msg in consumer:
            if _stop_event.is_set():
                break
            try:
                loop.run_until_complete(_send_notifications(msg.value))
            except Exception as exc:
                logger.error("Error processing message: %s", exc)

        consumer.close()
    except KafkaError as exc:
        logger.warning("Kafka not available: %s", exc)
    except Exception as exc:
        logger.error("Consumer error: %s", exc)
    finally:
        loop.close()


def start_consumer_thread() -> threading.Thread:
    thread = threading.Thread(target=run_consumer, daemon=True, name="notification-consumer")
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
