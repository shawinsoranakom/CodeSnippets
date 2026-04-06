async def _sse_producer_cm() -> AsyncIterator[
                    ObjectReceiveStream[bytes]
                ]:
                    # Use a memory stream to decouple generator iteration
                    # from the keepalive timer. A producer task pulls items
                    # from the generator independently, so
                    # `anyio.fail_after` never wraps the generator's
                    # `__anext__` directly - avoiding CancelledError that
                    # would finalize the generator and also working for sync
                    # generators running in a thread pool.
                    #
                    # This context manager is entered on the request-scoped
                    # AsyncExitStack so its __aexit__ (which cancels the
                    # task group) is called by the exit stack after the
                    # streaming response completes — not by async generator
                    # finalization via GeneratorExit.
                    # Ref: https://peps.python.org/pep-0789/
                    send_stream, receive_stream = anyio.create_memory_object_stream[
                        bytes
                    ](max_buffer_size=1)

                    async def _producer() -> None:
                        async with send_stream:
                            async for raw_item in sse_aiter:
                                await send_stream.send(_serialize_sse_item(raw_item))

                    send_keepalive, receive_keepalive = (
                        anyio.create_memory_object_stream[bytes](max_buffer_size=1)
                    )

                    async def _keepalive_inserter() -> None:
                        """Read from the producer and forward to the output,
                        inserting keepalive comments on timeout."""
                        async with send_keepalive, receive_stream:
                            try:
                                while True:
                                    try:
                                        with anyio.fail_after(_PING_INTERVAL):
                                            data = await receive_stream.receive()
                                        await send_keepalive.send(data)
                                    except TimeoutError:
                                        await send_keepalive.send(KEEPALIVE_COMMENT)
                            except anyio.EndOfStream:
                                pass

                    async with anyio.create_task_group() as tg:
                        tg.start_soon(_producer)
                        tg.start_soon(_keepalive_inserter)
                        yield receive_keepalive
                        tg.cancel_scope.cancel()