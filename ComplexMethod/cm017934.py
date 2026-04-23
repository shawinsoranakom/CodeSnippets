def convert_stream(
        self,
        stream: BinaryIO,
        *,
        stream_info: Optional[StreamInfo] = None,
        file_extension: Optional[str] = None,  # Deprecated -- use stream_info
        url: Optional[str] = None,  # Deprecated -- use stream_info
        **kwargs: Any,
    ) -> DocumentConverterResult:
        guesses: List[StreamInfo] = []

        # Do we have anything on which to base a guess?
        base_guess = None
        if stream_info is not None or file_extension is not None or url is not None:
            # Start with a non-Null base guess
            if stream_info is None:
                base_guess = StreamInfo()
            else:
                base_guess = stream_info

            if file_extension is not None:
                # Deprecated -- use stream_info
                assert base_guess is not None  # for mypy
                base_guess = base_guess.copy_and_update(extension=file_extension)

            if url is not None:
                # Deprecated -- use stream_info
                assert base_guess is not None  # for mypy
                base_guess = base_guess.copy_and_update(url=url)

        # Check if we have a seekable stream. If not, load the entire stream into memory.
        if not stream.seekable():
            buffer = io.BytesIO()
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                buffer.write(chunk)
            buffer.seek(0)
            stream = buffer

        # Add guesses based on stream content
        guesses = self._get_stream_info_guesses(
            file_stream=stream, base_guess=base_guess or StreamInfo()
        )
        return self._convert(file_stream=stream, stream_info_guesses=guesses, **kwargs)