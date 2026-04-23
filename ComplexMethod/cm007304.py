def decode_png(png_data):
    # Reference: https://www.w3.org/TR/PNG/
    header = png_data[8:]

    if png_data[:8] != b'\x89PNG\x0d\x0a\x1a\x0a' or header[4:8] != b'IHDR':
        raise IOError('Not a valid PNG file.')

    int_map = {1: '>B', 2: '>H', 4: '>I'}
    unpack_integer = lambda x: compat_struct_unpack(int_map[len(x)], x)[0]

    chunks = []

    while header:
        length = unpack_integer(header[:4])
        header = header[4:]

        chunk_type = header[:4]
        header = header[4:]

        chunk_data = header[:length]
        header = header[length:]

        header = header[4:]  # Skip CRC

        chunks.append({
            'type': chunk_type,
            'length': length,
            'data': chunk_data
        })

    ihdr = chunks[0]['data']

    width = unpack_integer(ihdr[:4])
    height = unpack_integer(ihdr[4:8])

    idat = b''

    for chunk in chunks:
        if chunk['type'] == b'IDAT':
            idat += chunk['data']

    if not idat:
        raise IOError('Unable to read PNG data.')

    decompressed_data = bytearray(zlib.decompress(idat))

    stride = width * 3
    pixels = []

    def _get_pixel(idx):
        x = idx % stride
        y = idx // stride
        return pixels[y][x]

    for y in range(height):
        basePos = y * (1 + stride)
        filter_type = decompressed_data[basePos]

        current_row = []

        pixels.append(current_row)

        for x in range(stride):
            color = decompressed_data[1 + basePos + x]
            basex = y * stride + x
            left = 0
            up = 0

            if x > 2:
                left = _get_pixel(basex - 3)
            if y > 0:
                up = _get_pixel(basex - stride)

            if filter_type == 1:  # Sub
                color = (color + left) & 0xff
            elif filter_type == 2:  # Up
                color = (color + up) & 0xff
            elif filter_type == 3:  # Average
                color = (color + ((left + up) >> 1)) & 0xff
            elif filter_type == 4:  # Paeth
                a = left
                b = up
                c = 0

                if x > 2 and y > 0:
                    c = _get_pixel(basex - stride - 3)

                p = a + b - c

                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)

                if pa <= pb and pa <= pc:
                    color = (color + a) & 0xff
                elif pb <= pc:
                    color = (color + b) & 0xff
                else:
                    color = (color + c) & 0xff

            current_row.append(color)

    return width, height, pixels