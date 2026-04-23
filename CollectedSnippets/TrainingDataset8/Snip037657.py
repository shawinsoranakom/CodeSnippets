def get_encoded_file_data(data, encoding="auto"):
    """Coerce bytes to a BytesIO or a StringIO.

    Parameters
    ----------
    data : bytes
    encoding : str

    Returns
    -------
    BytesIO or StringIO
        If the file's data is in a well-known textual format (or if the encoding
        parameter is set), return a StringIO. Otherwise, return BytesIO.

    """
    if encoding == "auto":
        if is_binary_string(data):
            encoding = None
        else:
            # If the file does not look like a pure binary file, assume
            # it's utf-8. It would be great if we could guess it a little
            # more smartly here, but it is what it is!
            encoding = "utf-8"

    if encoding:
        return io.StringIO(data.decode(encoding))

    return io.BytesIO(data)