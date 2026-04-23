def encode_multipart(boundary, data):
    """
    Encode multipart POST data from a dictionary of form values.

    The key will be used as the form data name; the value will be transmitted
    as content. If the value is a file, the contents of the file will be sent
    as an application/octet-stream; otherwise, str(value) will be sent.
    """
    lines = []

    def to_bytes(s):
        return force_bytes(s, settings.DEFAULT_CHARSET)

    # Not by any means perfect, but good enough for our purposes.
    def is_file(thing):
        return hasattr(thing, "read") and callable(thing.read)

    # Each bit of the multipart form data could be either a form value or a
    # file, or a *list* of form values and/or files. Remember that HTTP field
    # names can be duplicated!
    for key, value in data.items():
        if value is None:
            raise TypeError(
                "Cannot encode None for key '%s' as POST data. Did you mean "
                "to pass an empty string or omit the value?" % key
            )
        elif is_file(value):
            lines.extend(encode_file(boundary, key, value))
        elif not isinstance(value, str) and isinstance(value, Iterable):
            for item in value:
                if is_file(item):
                    lines.extend(encode_file(boundary, key, item))
                else:
                    lines.extend(
                        to_bytes(val)
                        for val in [
                            "--%s" % boundary,
                            'Content-Disposition: form-data; name="%s"' % key,
                            "",
                            item,
                        ]
                    )
        else:
            lines.extend(
                to_bytes(val)
                for val in [
                    "--%s" % boundary,
                    'Content-Disposition: form-data; name="%s"' % key,
                    "",
                    value,
                ]
            )

    lines.extend(
        [
            to_bytes("--%s--" % boundary),
            b"",
        ]
    )
    return b"\r\n".join(lines)