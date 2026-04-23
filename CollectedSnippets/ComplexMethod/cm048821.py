def _assert_handshake_validity(cls, headers):
        """
        :raise: UpgradeRequired if there is no intersection between
        the version the client supports and those we support.
        :raise: BadRequest in case of invalid handshake.
        """
        missing_or_empty_headers = {
            header for header in cls._REQUIRED_HANDSHAKE_HEADERS
            if header not in headers
        }
        if missing_or_empty_headers:
            raise BadRequest(
                f"""Empty or missing header(s): {', '.join(missing_or_empty_headers)}"""
            )

        if headers['upgrade'].lower() != 'websocket':
            raise BadRequest('Invalid upgrade header')
        if 'upgrade' not in headers['connection'].lower():
            raise BadRequest('Invalid connection header')
        if headers['sec-websocket-version'] not in cls.SUPPORTED_VERSIONS:
            raise UpgradeRequired()

        key = headers['sec-websocket-key']
        try:
            decoded_key = base64.b64decode(key, validate=True)
        except ValueError:
            raise BadRequest("Sec-WebSocket-Key should be b64 encoded")
        if len(decoded_key) != 16:
            raise BadRequest(
                "Sec-WebSocket-Key should be of length 16 once decoded"
            )