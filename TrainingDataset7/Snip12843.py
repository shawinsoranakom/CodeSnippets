def parse_boundary_stream(stream, max_header_size):
    """
    Parse one and exactly one stream that encapsulates a boundary.
    """

    # Look for the end of headers and if not found extend the search to double
    # the size up to the MAX_TOTAL_HEADER_SIZE.
    headers_chunk_size = 1024
    while True:
        if headers_chunk_size > max_header_size:
            raise MultiPartParserError("Request max total header size exceeded.")

        # Stream at beginning of header, look for end of header and parse it if
        # found. The header must fit within one chunk.
        chunk = stream.read(headers_chunk_size)
        # 'find' returns the top of these four bytes, so munch them later to
        # prevent them from polluting the payload.
        header_end = chunk.find(b"\r\n\r\n")
        if header_end != -1:
            break

        # Find no header, mark this fact and pass on the stream verbatim.
        stream.unget(chunk)
        # No more data to read.
        if len(chunk) < headers_chunk_size:
            return (RAW, {}, stream)
        # Double the chunk size.
        headers_chunk_size *= 2

    header = chunk[:header_end]

    # here we place any excess chunk back onto the stream, as
    # well as throwing away the CRLFCRLF bytes from above.
    stream.unget(chunk[header_end + 4 :])

    TYPE = RAW
    outdict = {}

    # Eliminate blank lines
    for line in header.split(b"\r\n"):
        try:
            header_name, value_and_params = line.decode().split(":", 1)
            name = header_name.lower().rstrip(" ")
            value, params = parse_header_parameters(value_and_params.lstrip(" "))
            params = {k: v.encode() for k, v in params.items()}
        except (ValueError, LookupError):  # Invalid header.
            continue

        if name == "content-disposition":
            TYPE = FIELD
            if params.get("filename"):
                TYPE = FILE

        outdict[name] = value, params

    if TYPE == RAW:
        stream.unget(chunk)

    return (TYPE, outdict, stream)