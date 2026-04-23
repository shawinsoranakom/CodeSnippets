async def _upload_multipart(
        self,
        tar_filename: str,
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        on_progress: OnProgressCallback,
    ) -> None:
        """Upload a large file using multipart upload.

        :param tar_filename: The target filename for the backup.
        :param open_stream: A function returning an async iterator that yields bytes.
        :param on_progress: A callback to report the number of uploaded bytes.
        """
        _LOGGER.debug("Starting multipart upload for %s", tar_filename)
        multipart_upload = await self._client.create_multipart_upload(
            Bucket=self._bucket,
            Key=self._with_prefix(tar_filename),
        )
        upload_id = multipart_upload["UploadId"]
        try:
            parts: list[dict[str, Any]] = []
            part_number = 1
            buffer = bytearray()  # bytes buffer to store the data
            offset = 0  # start index of unread data inside buffer
            bytes_uploaded = 0

            stream = await open_stream()
            async for chunk in stream:
                buffer.extend(chunk)

                # Upload parts of exactly MULTIPART_MIN_PART_SIZE_BYTES to ensure
                # all non-trailing parts have the same size (defensive implementation)
                view = memoryview(buffer)
                try:
                    while len(buffer) - offset >= MULTIPART_MIN_PART_SIZE_BYTES:
                        start = offset
                        end = offset + MULTIPART_MIN_PART_SIZE_BYTES
                        part_data = view[start:end]
                        offset = end

                        _LOGGER.debug(
                            "Uploading part number %d, size %d",
                            part_number,
                            len(part_data),
                        )
                        part = await cast(Any, self._client).upload_part(
                            Bucket=self._bucket,
                            Key=self._with_prefix(tar_filename),
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=part_data.tobytes(),
                        )
                        parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                        bytes_uploaded += len(part_data)
                        on_progress(bytes_uploaded=bytes_uploaded)
                        part_number += 1
                finally:
                    view.release()

                # Compact the buffer if the consumed offset has grown large enough. This
                # avoids unnecessary memory copies when compacting after every part upload.
                if offset and offset >= MULTIPART_MIN_PART_SIZE_BYTES:
                    buffer = bytearray(buffer[offset:])
                    offset = 0

            # Upload the final buffer as the last part (no minimum size requirement)
            # Offset should be 0 after the last compaction, but we use it as the start
            # index to be defensive in case the buffer was not compacted.
            if offset < len(buffer):
                remaining_data = memoryview(buffer)[offset:]
                _LOGGER.debug(
                    "Uploading final part number %d, size %d",
                    part_number,
                    len(remaining_data),
                )
                part = await cast(Any, self._client).upload_part(
                    Bucket=self._bucket,
                    Key=self._with_prefix(tar_filename),
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=remaining_data.tobytes(),
                )
                parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                bytes_uploaded += len(remaining_data)
                on_progress(bytes_uploaded=bytes_uploaded)

            await cast(Any, self._client).complete_multipart_upload(
                Bucket=self._bucket,
                Key=self._with_prefix(tar_filename),
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        except BotoCoreError:
            try:
                await self._client.abort_multipart_upload(
                    Bucket=self._bucket,
                    Key=self._with_prefix(tar_filename),
                    UploadId=upload_id,
                )
            except BotoCoreError:
                _LOGGER.exception("Failed to abort multipart upload")
            raise