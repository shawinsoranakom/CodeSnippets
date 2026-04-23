def image_to_url(
    image: AtomicImage,
    width: int,
    clamp: bool,
    channels: Channels,
    output_format: ImageFormatOrAuto,
    image_id: str,
) -> str:
    """Return a URL that an image can be served from.
    If `image` is already a URL, return it unmodified.
    Otherwise, add the image to the MediaFileManager and return the URL.

    (When running in "raw" mode, we won't actually load data into the
    MediaFileManager, and we'll return an empty URL.)
    """

    image_data: bytes

    # Strings
    if isinstance(image, str):
        # If it's a url, return it directly.
        try:
            p = urlparse(image)
            if p.scheme:
                return image
        except UnicodeDecodeError:
            # If the string runs into a UnicodeDecodeError, we assume it is not a valid URL.
            pass

        # Otherwise, try to open it as a file.
        try:
            with open(image, "rb") as f:
                image_data = f.read()
        except Exception:
            # When we aren't able to open the image file, we still pass the path to
            # the MediaFileManager - its storage backend may have access to files
            # that Streamlit does not.
            mimetype, _ = mimetypes.guess_type(image)
            if mimetype is None:
                mimetype = "application/octet-stream"

            url = runtime.get_instance().media_file_mgr.add(image, mimetype, image_id)
            caching.save_media_data(image, mimetype, image_id)
            return url

    # PIL Images
    elif isinstance(image, (ImageFile.ImageFile, Image.Image)):
        format = _validate_image_format_string(image, output_format)
        image_data = _PIL_to_bytes(image, format)

    # BytesIO
    # Note: This doesn't support SVG. We could convert to png (cairosvg.svg2png)
    # or just decode BytesIO to string and handle that way.
    elif isinstance(image, io.BytesIO):
        image_data = _BytesIO_to_bytes(image)

    # Numpy Arrays (ie opencv)
    elif isinstance(image, np.ndarray):
        image = _clip_image(
            _verify_np_shape(image),
            clamp,
        )

        if channels == "BGR":
            if len(image.shape) == 3:
                image = image[:, :, [2, 1, 0]]
            else:
                raise StreamlitAPIException(
                    'When using `channels="BGR"`, the input image should '
                    "have exactly 3 color channels"
                )

        # Depending on the version of numpy that the user has installed, the
        # typechecker may not be able to deduce that indexing into a
        # `npt.NDArray[Any]` returns a `npt.NDArray[Any]`, so we need to
        # ignore redundant casts below.
        image_data = _np_array_to_bytes(
            array=cast("npt.NDArray[Any]", image),  # type: ignore[redundant-cast]
            output_format=output_format,
        )

    # Raw bytes
    else:
        image_data = image

    # Determine the image's format, resize it, and get its mimetype
    image_format = _validate_image_format_string(image_data, output_format)
    image_data = _ensure_image_size_and_format(image_data, width, image_format)
    mimetype = _get_image_format_mimetype(image_format)

    if runtime.exists():
        url = runtime.get_instance().media_file_mgr.add(image_data, mimetype, image_id)
        caching.save_media_data(image_data, mimetype, image_id)
        return url
    else:
        # When running in "raw mode", we can't access the MediaFileManager.
        return ""