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