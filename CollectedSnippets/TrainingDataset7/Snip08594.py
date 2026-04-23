async def read_body(self, receive):
        """Reads an HTTP body from an ASGI connection."""
        # Use the tempfile that auto rolls-over to a disk file as it fills up.
        body_file = tempfile.SpooledTemporaryFile(
            max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE, mode="w+b"
        )
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                body_file.close()
                # Early client disconnect.
                raise RequestAborted()
            # Add a body chunk from the message, if provided.
            if "body" in message:
                on_disk = getattr(body_file, "_rolled", False)
                if on_disk:
                    async_write = sync_to_async(
                        body_file.write,
                        thread_sensitive=False,
                    )
                    await async_write(message["body"])
                else:
                    body_file.write(message["body"])

            # Quit out if that's the end.
            if not message.get("more_body", False):
                break
        body_file.seek(0)
        return body_file