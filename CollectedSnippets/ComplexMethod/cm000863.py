def _consume_cancel(self):
        """Consume cancellation messages from FANOUT exchange."""
        if self.stop_consuming.is_set() and not self.active_tasks:
            logger.info("Stop reconnecting cancel consumer - service cleaned up")
            return

        if not self.cancel_client.is_ready:
            self.cancel_client.disconnect()
        self.cancel_client.connect()

        # Check again after connect - shutdown may have been requested
        if self.stop_consuming.is_set() and not self.active_tasks:
            logger.info("Stop consuming requested during reconnect - disconnecting")
            self.cancel_client.disconnect()
            return

        cancel_channel = self.cancel_client.get_channel()
        cancel_channel.basic_consume(
            queue=COPILOT_CANCEL_QUEUE_NAME,
            on_message_callback=self._handle_cancel_message,
            auto_ack=True,
        )
        logger.info("Starting to consume cancel messages...")
        cancel_channel.start_consuming()
        if not self.stop_consuming.is_set() or self.active_tasks:
            raise RuntimeError("Cancel message consumer stopped unexpectedly")
        logger.info("Cancel message consumer stopped gracefully")