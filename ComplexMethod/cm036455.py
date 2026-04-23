def load_image(
    data: list[str],
    path_type: str,
    mean: list[float] | None = None,
    std: list[float] | None = None,
    indices: list[int] | None | None = None,
):
    """Build an input example by loading images in *file_paths*.

    Args:
        file_paths: list of file paths .
        mean: list containing mean values for each band in the
              images in *file_paths*.
        std: list containing std values for each band in the
             images in *file_paths*.

    Returns:
        np.array containing created example
        list of meta info for each image in *file_paths*
    """

    imgs = []
    metas = []
    temporal_coords = []
    location_coords = []

    for file in data:
        # if isinstance(file, bytes):
        #     img, meta, coords = read_geotiff(file_data=file)
        # else:
        img, meta, coords = read_geotiff(file_path=file, path_type=path_type)
        # Rescaling (don't normalize on nodata)
        img = np.moveaxis(img, 0, -1)  # channels last for rescaling
        if indices is not None:
            img = img[..., indices]
        if mean is not None and std is not None:
            img = np.where(img == NO_DATA, NO_DATA_FLOAT, (img - mean) / std)

        imgs.append(img)
        metas.append(meta)
        if coords is not None:
            location_coords.append(coords)

        try:
            match = re.search(r"(\d{7,8}T\d{6})", file)
            if match:
                year = int(match.group(1)[:4])
                julian_day = match.group(1).split("T")[0][4:]
                if len(julian_day) == 3:
                    julian_day = int(julian_day)
                else:
                    julian_day = (
                        datetime.datetime.strptime(julian_day, "%m%d")
                        .timetuple()
                        .tm_yday
                    )
                temporal_coords.append([year, julian_day])
        except Exception:
            logger.exception("Could not extract timestamp for %s", file)

    imgs = np.stack(imgs, axis=0)  # num_frames, H, W, C
    imgs = np.moveaxis(imgs, -1, 0).astype("float32")  # C, num_frames, H, W
    imgs = np.expand_dims(imgs, axis=0)  # add batch di

    return imgs, temporal_coords, location_coords, metas