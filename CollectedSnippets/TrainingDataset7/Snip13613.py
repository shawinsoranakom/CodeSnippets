def encode_file(boundary, key, file):
    def to_bytes(s):
        return force_bytes(s, settings.DEFAULT_CHARSET)

    # file.name might not be a string. For example, it's an int for
    # tempfile.TemporaryFile().
    file_has_string_name = hasattr(file, "name") and isinstance(file.name, str)
    filename = os.path.basename(file.name) if file_has_string_name else ""

    if hasattr(file, "content_type"):
        content_type = file.content_type
    elif filename:
        content_type = mimetypes.guess_type(filename)[0]
    else:
        content_type = None

    if content_type is None:
        content_type = "application/octet-stream"
    filename = filename or key
    return [
        to_bytes("--%s" % boundary),
        to_bytes(
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename)
        ),
        to_bytes("Content-Type: %s" % content_type),
        b"",
        to_bytes(file.read()),
    ]