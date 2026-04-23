def consume_messages(self, max_messages: int = 10, timeout: float = 5.0):
        """Consume messages and track their order."""

        def callback(ch, method, properties, body):
            try:
                message_data = json.loads(body.decode())
                self.received_messages.append(message_data)
                ch.basic_ack(delivery_tag=method.delivery_tag)

                if len(self.received_messages) >= max_messages:
                    self.stop_consuming.set()
            except Exception as e:
                print(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # Use synchronous consumption with blocking
        channel = self.queue_client.get_channel()

        # Check if there are messages in the queue first
        method_frame, header_frame, body = channel.basic_get(
            queue=self.test_queue_name, auto_ack=False
        )
        if method_frame:
            # There are messages, set up consumer
            channel.basic_nack(
                delivery_tag=method_frame.delivery_tag, requeue=True
            )  # Put message back

            # Set up consumer
            channel.basic_consume(
                queue=self.test_queue_name,
                on_message_callback=callback,
            )

            # Consume with timeout
            start_time = time.time()
            while (
                not self.stop_consuming.is_set()
                and (time.time() - start_time) < timeout
                and len(self.received_messages) < max_messages
            ):
                try:
                    channel.connection.process_data_events(time_limit=0.1)
                except Exception as e:
                    print(f"Error during consumption: {e}")
                    break

            # Cancel the consumer
            try:
                channel.cancel()
            except Exception:
                pass
        else:
            # No messages in queue - this might be expected for some tests
            pass

        return self.received_messages

    def cleanup(self):
        """Clean up test resources."""
        try:
            channel = self.queue_client.get_channel()
            channel.queue_delete(queue=self.test_queue_name)
            channel.exchange_delete(exchange=self.test_exchange)
            print(f"✅ Test queue {self.test_queue_name} cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup issue: {e}")
