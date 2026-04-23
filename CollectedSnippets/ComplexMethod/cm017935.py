def convert_uri(
        self,
        uri: str,
        *,
        stream_info: Optional[StreamInfo] = None,
        file_extension: Optional[str] = None,  # Deprecated -- use stream_info
        mock_url: Optional[
            str
        ] = None,  # Mock the request as if it came from a different URL
        **kwargs: Any,
    ) -> DocumentConverterResult:
        uri = uri.strip()

        # File URIs
        if uri.startswith("file:"):
            netloc, path = file_uri_to_path(uri)
            if netloc and netloc != "localhost":
                raise ValueError(
                    f"Unsupported file URI: {uri}. Netloc must be empty or localhost."
                )
            return self.convert_local(
                path,
                stream_info=stream_info,
                file_extension=file_extension,
                url=mock_url,
                **kwargs,
            )
        # Data URIs
        elif uri.startswith("data:"):
            mimetype, attributes, data = parse_data_uri(uri)

            base_guess = StreamInfo(
                mimetype=mimetype,
                charset=attributes.get("charset"),
            )
            if stream_info is not None:
                base_guess = base_guess.copy_and_update(stream_info)

            return self.convert_stream(
                io.BytesIO(data),
                stream_info=base_guess,
                file_extension=file_extension,
                url=mock_url,
                **kwargs,
            )
        # HTTP/HTTPS URIs
        elif uri.startswith("http:") or uri.startswith("https:"):
            response = self._requests_session.get(uri, stream=True)
            response.raise_for_status()
            return self.convert_response(
                response,
                stream_info=stream_info,
                file_extension=file_extension,
                url=mock_url,
                **kwargs,
            )
        else:
            raise ValueError(
                f"Unsupported URI scheme: {uri.split(':')[0]}. Supported schemes are: file:, data:, http:, https:"
            )