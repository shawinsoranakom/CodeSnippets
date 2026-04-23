def _get_request_headers(self) -> list[tuple[str, str]]:
        url = urlparse_cached(self._request)

        path = url.path
        if url.query:
            path += "?" + url.query

        # This pseudo-header field MUST NOT be empty for "http" or "https"
        # URIs; "http" or "https" URIs that do not contain a path component
        # MUST include a value of '/'. The exception to this rule is an
        # OPTIONS request for an "http" or "https" URI that does not include
        # a path component; these MUST include a ":path" pseudo-header field
        # with a value of '*' (refer RFC 7540 - Section 8.1.2.3)
        if not path:
            path = "*" if self._request.method == "OPTIONS" else "/"

        # Make sure pseudo-headers comes before all the other headers
        headers = [
            (":method", self._request.method),
            (":authority", url.netloc),
        ]

        # The ":scheme" and ":path" pseudo-header fields MUST
        # be omitted for CONNECT method (refer RFC 7540 - Section 8.3)
        if self._request.method != "CONNECT":
            headers += [
                (":scheme", self._protocol.metadata["uri"].scheme),
                (":path", path),
            ]

        content_length = str(len(self._request.body))
        headers.append(("Content-Length", content_length))

        content_length_name = self._request.headers.normkey(b"Content-Length")
        for name, values in self._request.headers.items():
            for value_bytes in values:
                value = str(value_bytes, "utf-8")
                if name == content_length_name:
                    if value != content_length:
                        logger.warning(
                            "Ignoring bad Content-Length header %r of request %r, "
                            "sending %r instead",
                            value,
                            self._request,
                            content_length,
                        )
                    continue
                headers.append((str(name, "utf-8"), value))

        return headers