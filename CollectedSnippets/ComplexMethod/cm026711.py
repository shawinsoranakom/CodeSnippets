async def _upload_file(self, request: web.Request) -> web.Response:
        """Handle uploaded file."""
        # Increase max payload
        request._client_max_size = MAX_SIZE  # noqa: SLF001

        reader = await request.multipart()
        file_field_reader = await reader.next()
        filename: str | None

        if (
            not isinstance(file_field_reader, BodyPartReader)
            or file_field_reader.name != "file"
            or (filename := file_field_reader.filename) is None
        ):
            raise vol.Invalid("Expected a file")

        try:
            raise_if_invalid_filename(filename)
        except ValueError as err:
            raise web.HTTPBadRequest from err

        hass = request.app[KEY_HASS]
        file_id = ulid_hex()

        if _DATA not in hass.data:
            hass.data[_DATA] = await FileUploadData.create(hass)

        file_upload_data = hass.data[_DATA]
        file_dir = file_upload_data.file_dir(file_id)
        queue: SimpleQueue[tuple[bytes, asyncio.Future[None] | None] | None] = (
            SimpleQueue()
        )

        def _sync_queue_consumer() -> None:
            file_dir.mkdir()
            with (file_dir / filename).open("wb") as file_handle:
                while True:
                    if (_chunk_future := queue.get()) is None:
                        break
                    _chunk, _future = _chunk_future
                    if _future is not None:
                        hass.loop.call_soon_threadsafe(_future.set_result, None)
                    file_handle.write(_chunk)

        fut: asyncio.Future[None] | None = None
        try:
            fut = hass.async_add_executor_job(_sync_queue_consumer)
            megabytes_sending = 0
            while chunk := await file_field_reader.read_chunk(ONE_MEGABYTE):
                megabytes_sending += 1
                if megabytes_sending % 5 != 0:
                    queue.put_nowait((chunk, None))
                    continue

                chunk_future = hass.loop.create_future()
                queue.put_nowait((chunk, chunk_future))
                await asyncio.wait(
                    (fut, chunk_future), return_when=asyncio.FIRST_COMPLETED
                )
                if fut.done():
                    # The executor job failed
                    break

            queue.put_nowait(None)  # terminate queue consumer
        finally:
            if fut is not None:
                await fut

        file_upload_data.files[file_id] = filename

        return self.json({"file_id": file_id})