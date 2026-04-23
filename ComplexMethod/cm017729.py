def _parse(self):
        """
        Parse the POST data and break it into a FILES MultiValueDict and a POST
        MultiValueDict.

        Return a tuple containing the POST and FILES dictionary, respectively.
        """
        from django.http import QueryDict

        encoding = self._encoding
        handlers = self._upload_handlers

        # HTTP spec says that Content-Length >= 0 is valid
        # handling content-length == 0 before continuing
        if self._content_length == 0:
            return QueryDict(encoding=self._encoding), MultiValueDict()

        # See if any of the handlers take care of the parsing.
        # This allows overriding everything if need be.
        for handler in handlers:
            result = handler.handle_raw_input(
                self._input_data,
                self._meta,
                self._content_length,
                self._boundary,
                encoding,
            )
            # Check to see if it was handled
            if result is not None:
                return result[0], result[1]

        # Create the data structures to be used later.
        self._post = QueryDict(mutable=True)
        self._files = MultiValueDict()

        # Instantiate the parser and stream:
        stream = LazyStream(ChunkIter(self._input_data, self._chunk_size))

        # Whether or not to signal a file-completion at the beginning of the
        # loop.
        old_field_name = None
        counters = [0] * len(handlers)

        # Number of bytes that have been read.
        num_bytes_read = 0
        # To count the number of keys in the request.
        num_post_keys = 0
        # To count the number of files in the request.
        num_files = 0
        # To limit the amount of data read from the request.
        read_size = None
        # Whether a file upload is finished.
        uploaded_file = True

        try:
            for item_type, meta_data, field_stream in Parser(stream, self._boundary):
                if old_field_name:
                    # We run this at the beginning of the next loop
                    # since we cannot be sure a file is complete until
                    # we hit the next boundary/part of the multipart content.
                    self.handle_file_complete(old_field_name, counters)
                    old_field_name = None
                    uploaded_file = True

                if (
                    item_type in FIELD_TYPES
                    and settings.DATA_UPLOAD_MAX_NUMBER_FIELDS is not None
                ):
                    # Avoid storing more than DATA_UPLOAD_MAX_NUMBER_FIELDS.
                    num_post_keys += 1
                    # 2 accounts for empty raw fields before and after the
                    # last boundary.
                    if settings.DATA_UPLOAD_MAX_NUMBER_FIELDS + 2 < num_post_keys:
                        raise TooManyFieldsSent(
                            "The number of GET/POST parameters exceeded "
                            "settings.DATA_UPLOAD_MAX_NUMBER_FIELDS."
                        )

                try:
                    disposition = meta_data["content-disposition"][1]
                    field_name = disposition["name"].strip()
                except (KeyError, IndexError, AttributeError):
                    continue

                transfer_encoding = meta_data.get("content-transfer-encoding")
                if transfer_encoding is not None:
                    transfer_encoding = transfer_encoding[0].strip()
                field_name = force_str(field_name, encoding, errors="replace")

                if item_type == FIELD:
                    # Avoid reading more than DATA_UPLOAD_MAX_MEMORY_SIZE.
                    if settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None:
                        read_size = (
                            settings.DATA_UPLOAD_MAX_MEMORY_SIZE - num_bytes_read
                        )

                    # This is a post field, we can just set it in the post
                    if transfer_encoding == "base64":
                        raw_data = field_stream.read(size=read_size)
                        num_bytes_read += len(raw_data)
                        try:
                            data = base64.b64decode(raw_data)
                        except binascii.Error:
                            data = raw_data
                    else:
                        data = field_stream.read(size=read_size)
                        num_bytes_read += len(data)

                    # Add two here to make the check consistent with the
                    # x-www-form-urlencoded check that includes '&='.
                    num_bytes_read += len(field_name) + 2
                    if (
                        settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None
                        and num_bytes_read > settings.DATA_UPLOAD_MAX_MEMORY_SIZE
                    ):
                        raise RequestDataTooBig(
                            "Request body exceeded "
                            "settings.DATA_UPLOAD_MAX_MEMORY_SIZE."
                        )

                    self._post.appendlist(
                        field_name, force_str(data, encoding, errors="replace")
                    )
                elif item_type == FILE:
                    # Avoid storing more than DATA_UPLOAD_MAX_NUMBER_FILES.
                    num_files += 1
                    if (
                        settings.DATA_UPLOAD_MAX_NUMBER_FILES is not None
                        and num_files > settings.DATA_UPLOAD_MAX_NUMBER_FILES
                    ):
                        raise TooManyFilesSent(
                            "The number of files exceeded "
                            "settings.DATA_UPLOAD_MAX_NUMBER_FILES."
                        )
                    # This is a file, use the handler...
                    file_name = disposition.get("filename")
                    if file_name:
                        file_name = force_str(file_name, encoding, errors="replace")
                        file_name = self.sanitize_file_name(file_name)
                    if not file_name:
                        continue

                    content_type, content_type_extra = meta_data.get(
                        "content-type", ("", {})
                    )
                    content_type = content_type.strip()
                    charset = content_type_extra.get("charset")

                    try:
                        content_length = int(meta_data.get("content-length")[0])
                    except (IndexError, TypeError, ValueError):
                        content_length = None

                    counters = [0] * len(handlers)
                    uploaded_file = False
                    try:
                        for handler in handlers:
                            try:
                                handler.new_file(
                                    field_name,
                                    file_name,
                                    content_type,
                                    content_length,
                                    charset,
                                    content_type_extra,
                                )
                            except StopFutureHandlers:
                                break

                        for chunk in field_stream:
                            if transfer_encoding == "base64":
                                # We only special-case base64 transfer encoding
                                # We should always decode base64 chunks by
                                # multiple of 4, ignoring whitespace.

                                stripped_parts = [b"".join(chunk.split())]
                                stripped_length = len(stripped_parts[0])

                                while stripped_length % 4 != 0:
                                    over_chunk = field_stream.read(self._chunk_size)
                                    if not over_chunk:
                                        break
                                    over_stripped = b"".join(over_chunk.split())
                                    stripped_parts.append(over_stripped)
                                    stripped_length += len(over_stripped)

                                stripped_chunk = b"".join(stripped_parts)

                                try:
                                    chunk = base64.b64decode(stripped_chunk)
                                except Exception as exc:
                                    # Since this is only a chunk, any error is
                                    # an unfixable error.
                                    raise MultiPartParserError(
                                        "Could not decode base64 data."
                                    ) from exc

                            for i, handler in enumerate(handlers):
                                chunk_length = len(chunk)
                                chunk = handler.receive_data_chunk(chunk, counters[i])
                                counters[i] += chunk_length
                                if chunk is None:
                                    # Don't continue if the chunk received by
                                    # the handler is None.
                                    break

                    except SkipFile:
                        self._close_files()
                        # Just use up the rest of this file...
                        exhaust(field_stream)
                    else:
                        # Handle file upload completions on next iteration.
                        old_field_name = field_name
                else:
                    # If this is neither a FIELD nor a FILE, exhaust the field
                    # stream. Note: There could be an error here at some point,
                    # but there will be at least two RAW types (before and
                    # after the other boundaries). This branch is usually not
                    # reached at all, because a missing content-disposition
                    # header will skip the whole boundary.
                    exhaust(field_stream)
        except StopUpload as e:
            self._close_files()
            if not e.connection_reset:
                exhaust(self._input_data)
        else:
            if not uploaded_file:
                for handler in handlers:
                    handler.upload_interrupted()
            # Make sure that the request data is all fed
            exhaust(self._input_data)

        # Signal that the upload has completed.
        # any() shortcircuits if a handler's upload_complete() returns a value.
        any(handler.upload_complete() for handler in handlers)
        self._post._mutable = False
        return self._post, self._files