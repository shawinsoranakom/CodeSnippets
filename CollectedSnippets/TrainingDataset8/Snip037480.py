def _np_array_to_bytes(array: "npt.NDArray[Any]", output_format="JPEG") -> bytes:
    img = Image.fromarray(array.astype(np.uint8))
    format = _validate_image_format_string(img, output_format)

    return _PIL_to_bytes(img, format)