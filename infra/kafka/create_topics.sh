#!/bin/bash
# Creates all Kafka topics on first startup
# kafka_init container runs this once and exits

set -e

KAFKA_BROKER="kafka:9092"

echo "Waiting for Kafka to be ready..."
sleep 10

echo "Creating Kafka topics..."

kafka-topics --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic user.registered \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic order.created \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic chef.assigned \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic delivery.started \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic delivery.completed \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "All topics created."

# verify
kafka-topics --list --bootstrap-server $KAFKA_BROKER