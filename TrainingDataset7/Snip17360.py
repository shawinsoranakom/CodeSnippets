async def streaming_response():
            nonlocal view_did_cancel
            try:
                await asyncio.sleep(0.2)
                yield b"Hello World!"
            except asyncio.CancelledError:
                # Set the flag.
                view_did_cancel = True
                raise