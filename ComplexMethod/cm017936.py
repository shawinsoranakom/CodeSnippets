def convert_response(
        self,
        response: requests.Response,
        *,
        stream_info: Optional[StreamInfo] = None,
        file_extension: Optional[str] = None,  # Deprecated -- use stream_info
        url: Optional[str] = None,  # Deprecated -- use stream_info
        **kwargs: Any,
    ) -> DocumentConverterResult:
        # If there is a content-type header, get the mimetype and charset (if present)
        mimetype: Optional[str] = None
        charset: Optional[str] = None

        if "content-type" in response.headers:
            parts = response.headers["content-type"].split(";")
            mimetype = parts.pop(0).strip()
            for part in parts:
                if part.strip().startswith("charset="):
                    _charset = part.split("=")[1].strip()
                    if len(_charset) > 0:
                        charset = _charset

        # If there is a content-disposition header, get the filename and possibly the extension
        filename: Optional[str] = None
        extension: Optional[str] = None
        if "content-disposition" in response.headers:
            m = re.search(r"filename=([^;]+)", response.headers["content-disposition"])
            if m:
                filename = m.group(1).strip("\"'")
                _, _extension = os.path.splitext(filename)
                if len(_extension) > 0:
                    extension = _extension

        # If there is still no filename, try to read it from the url
        if filename is None:
            parsed_url = urlparse(response.url)
            _, _extension = os.path.splitext(parsed_url.path)
            if len(_extension) > 0:  # Looks like this might be a file!
                filename = os.path.basename(parsed_url.path)
                extension = _extension

        # Create an initial guess from all this information
        base_guess = StreamInfo(
            mimetype=mimetype,
            charset=charset,
            filename=filename,
            extension=extension,
            url=response.url,
        )

        # Update with any additional info from the arguments
        if stream_info is not None:
            base_guess = base_guess.copy_and_update(stream_info)
        if file_extension is not None:
            # Deprecated -- use stream_info
            base_guess = base_guess.copy_and_update(extension=file_extension)
        if url is not None:
            # Deprecated -- use stream_info
            base_guess = base_guess.copy_and_update(url=url)

        # Read into BytesIO
        buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=512):
            buffer.write(chunk)
        buffer.seek(0)

        # Convert
        guesses = self._get_stream_info_guesses(
            file_stream=buffer, base_guess=base_guess
        )
        return self._convert(file_stream=buffer, stream_info_guesses=guesses, **kwargs)