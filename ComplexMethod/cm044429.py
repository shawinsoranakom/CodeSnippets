def read_image_meta(filename):
    """ Read the Faceswap metadata stored in an extracted face's exif header.

    Parameters
    ----------
    filename: str
        Full path to the image to be retrieve the meta information for.

    Returns
    -------
    dict
        The output dictionary will contain the `width` and `height` of the png image as well as any
        `itxt` information.
    Example
    -------
    >>> image_file = "/path/to/image.png"
    >>> metadata = read_image_meta(image_file)
    >>> width = metadata["width]
    >>> height = metadata["height"]
    >>> faceswap_info = metadata["itxt"]
    """
    retval = {}
    if os.path.splitext(filename)[-1].lower() != ".png":
        # Get the dimensions directly from the image for non-png
        logger.trace(  # type:ignore[attr-defined]
            "Non png found. Loading file for dimensions: '%s'",
            filename)
        img = cv2.imread(filename)
        assert img is not None
        retval["height"], retval["width"] = img.shape[:2]
        return retval
    with open(filename, "rb") as in_file:
        try:
            chunk = in_file.read(8)
        except PermissionError as exc:
            raise PermissionError(f"PermissionError while reading: {filename}") from exc

        if chunk != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Invalid header found in png: {filename}")

        while True:
            chunk = in_file.read(8)
            length, field = struct.unpack(">I4s", chunk)
            logger.trace(  # type:ignore[attr-defined]
                "Read chunk: (chunk: %s, length: %s, field: %s",
                chunk, length, field)
            if not chunk or field == b"IDAT":
                break
            if field == b"IHDR":
                # Get dimensions
                chunk = in_file.read(8)
                retval["width"], retval["height"] = struct.unpack(">II", chunk)
                length -= 8
            elif field == b"iTXt":
                keyword, value = in_file.read(length).split(b"\0", 1)
                if keyword == b"faceswap":
                    retval["itxt"] = literal_eval(value[4:].decode("utf-8", errors="replace"))
                    break
                logger.trace("Skipping iTXt chunk: '%s'",  # type:ignore[attr-defined]
                             keyword.decode("latin-1", errors="ignore"))
                length = 0  # Reset marker for next chunk
            in_file.seek(length + 4, 1)
    logger.trace("filename: %s, metadata: %s", filename, retval)  # type:ignore[attr-defined]
    return retval