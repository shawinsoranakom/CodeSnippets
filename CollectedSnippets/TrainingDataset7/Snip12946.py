def _convert_to_charset(self, value, charset, mime_encode=False):
        """
        Convert headers key/value to ascii/latin-1 native strings.
        `charset` must be 'ascii' or 'latin-1'. If `mime_encode` is True and
        `value` can't be represented in the given charset, apply MIME-encoding.
        """
        try:
            if isinstance(value, str):
                # Ensure string is valid in given charset
                value.encode(charset)
            elif isinstance(value, bytes):
                # Convert bytestring using given charset
                value = value.decode(charset)
            else:
                value = str(value)
                # Ensure string is valid in given charset.
                value.encode(charset)
            if "\n" in value or "\r" in value:
                raise BadHeaderError(
                    f"Header values can't contain newlines (got {value!r})"
                )
        except UnicodeError as e:
            # Encoding to a string of the specified charset failed, but we
            # don't know what type that value was, or if it contains newlines,
            # which we may need to check for before sending it to be
            # encoded for multiple character sets.
            if (isinstance(value, bytes) and (b"\n" in value or b"\r" in value)) or (
                isinstance(value, str) and ("\n" in value or "\r" in value)
            ):
                raise BadHeaderError(
                    f"Header values can't contain newlines (got {value!r})"
                ) from e
            if mime_encode:
                value = Header(value, "utf-8", maxlinelen=sys.maxsize).encode()
            else:
                e.reason += ", HTTP response headers must be in %s format" % charset
                raise
        return value