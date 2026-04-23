def read_geotiff(
    file_path: str | None = None,
    path_type: str | None = None,
    file_data: bytes | None = None,
) -> tuple[torch.Tensor, dict, tuple[float, float] | None]:
    """Read all bands from *file_path* and return image + meta info.

    Args:
        file_path: path to image file.

    Returns:
        np.ndarray with shape (bands, height, width)
        meta info dict
    """

    if all([x is None for x in [file_path, path_type, file_data]]):
        raise Exception("All input fields to read_geotiff are None")
    write_to_file: bytes | None = None
    path: str | None = None
    if file_data is not None:
        # with tempfile.NamedTemporaryFile() as tmpfile:
        #     tmpfile.write(file_data)
        #     path = tmpfile.name

        write_to_file = file_data
    elif file_path is not None and path_type == "url":
        resp = urllib.request.urlopen(file_path)
        # with tempfile.NamedTemporaryFile() as tmpfile:
        #     tmpfile.write(resp.read())
        #     path = tmpfile.name
        write_to_file = resp.read()
    elif file_path is not None and path_type == "path":
        path = file_path
    elif file_path is not None and path_type == "b64_json":
        image_data = base64.b64decode(file_path)
        # with tempfile.NamedTemporaryFile() as tmpfile:
        #     tmpfile.write(image_data)
        #     path = tmpfile.name
        write_to_file = image_data
    else:
        raise Exception("Wrong combination of parameters to read_geotiff")

    with tempfile.NamedTemporaryFile() as tmpfile:
        path_to_use = None
        if write_to_file:
            tmpfile.write(write_to_file)
            path_to_use = tmpfile.name
        elif path:
            path_to_use = path

        with rasterio.open(path_to_use) as src:
            img = src.read()
            meta = src.meta
            try:
                coords = src.lnglat()
            except Exception:
                # Cannot read coords
                coords = None

    return img, meta, coords