def body(self):
        if not hasattr(self, "_body"):
            if self._read_started:
                raise RawPostDataException(
                    "You cannot access body after reading from request's data stream"
                )

            # Limit the maximum request data size that will be handled
            # in-memory.
            if (
                settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None
                and int(self.META.get("CONTENT_LENGTH") or 0)
                > settings.DATA_UPLOAD_MAX_MEMORY_SIZE
            ):
                raise RequestDataTooBig(
                    "Request body exceeded settings.DATA_UPLOAD_MAX_MEMORY_SIZE."
                )

            try:
                self._body = self.read()
            except OSError as e:
                raise UnreadablePostError(*e.args) from e
            finally:
                self._stream.close()
            self._stream = BytesIO(self._body)
        return self._body