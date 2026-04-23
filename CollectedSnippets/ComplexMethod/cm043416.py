def apply_png_predictor(data, width, bits, color_channels):
    """Decode PNG predictor (PDF 1.5+ filter)"""
    bytes_per_pixel = (bits * color_channels) // 8
    if (bits * color_channels) % 8 != 0:
        bytes_per_pixel += 1

    stride = width * bytes_per_pixel
    scanline_length = stride + 1  # +1 for filter byte

    if len(data) % scanline_length != 0:
        raise ValueError("Invalid scanline structure")

    num_lines = len(data) // scanline_length
    output = bytearray()
    prev_line = b'\x00' * stride

    for i in range(num_lines):
        line = data[i*scanline_length:(i+1)*scanline_length]
        filter_type = line[0]
        filtered = line[1:]

        if filter_type == 0:  # None
            decoded = filtered
        elif filter_type == 1:  # Sub
            decoded = bytearray(filtered)
            for j in range(bytes_per_pixel, len(decoded)):
                decoded[j] = (decoded[j] + decoded[j - bytes_per_pixel]) % 256
        elif filter_type == 2:  # Up
            decoded = bytearray([(filtered[j] + prev_line[j]) % 256 
                               for j in range(len(filtered))])
        elif filter_type == 3:  # Average
            decoded = bytearray(filtered)
            for j in range(len(decoded)):
                left = decoded[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                up = prev_line[j]
                avg = (left + up) // 2
                decoded[j] = (decoded[j] + avg) % 256
        elif filter_type == 4:  # Paeth
            decoded = bytearray(filtered)
            for j in range(len(decoded)):
                left = decoded[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                up = prev_line[j]
                up_left = prev_line[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                paeth = paeth_predictor(left, up, up_left)
                decoded[j] = (decoded[j] + paeth) % 256
        else:
            raise ValueError(f"Unsupported filter type: {filter_type}")

        output.extend(decoded)
        prev_line = decoded

    return bytes(output)