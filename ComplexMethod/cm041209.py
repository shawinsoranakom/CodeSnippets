def _parse_shape(
        self, request: Request, shape: Shape, node: Any, uri_params: Mapping[str, Any] = None
    ) -> Any:
        """
        Special handling of parsing the shape for s3 object-names (=key):
        Trailing '/' are valid and need to be preserved, however, the url-matcher removes it from the key.
        We need special logic to compare the parsed Key parameter against the path and add back the missing slashes
        """
        if (
            shape is not None
            and uri_params is not None
            and shape.serialization.get("location") == "uri"
            and shape.serialization.get("name") == "Key"
            and (
                (trailing_slashes := request.path.rpartition(uri_params["Key"])[2])
                and all(char == "/" for char in trailing_slashes)
            )
        ):
            uri_params = dict(uri_params)
            uri_params["Key"] = uri_params["Key"] + trailing_slashes
        return super()._parse_shape(request, shape, node, uri_params)