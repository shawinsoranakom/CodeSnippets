async def _consume_queue(
        self,
        queue: aio_pika.abc.AbstractQueue,
        process_func: Callable[[str], Awaitable[bool]],
        queue_name: str,
    ):
        """Continuously consume messages from a queue using async iteration"""
        logger.info(f"Starting consumer for queue: {queue_name}")

        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self.running:
                        break

                    try:
                        async with message.process():
                            result = await process_func(message.body.decode())
                            if not result:
                                # Message will be rejected when exiting context without exception
                                raise aio_pika.exceptions.MessageProcessError(
                                    "Processing failed"
                                )
                    except aio_pika.exceptions.MessageProcessError:
                        # Let message.process() handle the rejection
                        pass
                    except Exception as e:
                        logger.warning(
                            f"Error processing message in {queue_name}: {e}",
                            exc_info=True,
                        )
                        # Let message.process() handle the rejection
                        raise
        except asyncio.CancelledError:
            logger.info(f"Consumer for {queue_name} cancelled")
            raise
        except Exception as e:
            logger.exception(f"Fatal error in consumer for {queue_name}: {e}")
            raise