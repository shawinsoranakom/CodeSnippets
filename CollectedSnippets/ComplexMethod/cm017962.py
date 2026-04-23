def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in CANDIDATE_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                # Read further to see if it's a notebook
                cur_pos = file_stream.tell()
                try:
                    encoding = stream_info.charset or "utf-8"
                    notebook_content = file_stream.read().decode(encoding)
                    return (
                        "nbformat" in notebook_content
                        and "nbformat_minor" in notebook_content
                    )
                finally:
                    file_stream.seek(cur_pos)

        return False