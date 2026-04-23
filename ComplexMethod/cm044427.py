def read_image(filename: str,  # noqa[C901]  # pylint:disable=too-many-statements,too-many-branches
               raise_error: bool = False,
               with_metadata: bool = False
               ) -> np.ndarray | None | tuple[npt.NDArray[np.uint8], PNGHeader]:
    """Read an image file from a file location.

    Extends the functionality of :func:`cv2.imread()` by ensuring that an image was actually
    loaded. Errors can be logged and ignored so that the process can continue on an image load
    failure.

    Parameters
    ----------
    filename
        Full path to the image to be loaded.
    raise_error
        If ``True`` then any failures (including the returned image being ``None``) will be
        raised. If ``False`` then an error message will be logged, but the error will not be
        raised. Default: ``False``
    with_metadata
        Only returns a value if the images loaded are extracted Faceswap faces. If ``True`` then
        returns the Faceswap metadata stored with in a Face images .png EXIF header.
        Default: ``False``

    Returns
    -------
    image
        The image in `BGR` channel order as UINT8 for the corresponding :attr:`filename`
    metadata
        The faceswap metadata corresponding to the image. Only returned if
        `with_metadata` is ``True``

    Example
    -------
    >>> image_file = "/path/to/image.png"
    >>> try:
    >>>    image = read_image(image_file, raise_error=True, with_metadata=False)
    >>> except:
    >>>     raise ValueError("There was an error")
    """
    logger.trace("Requested image: '%s'", filename)  # type:ignore[attr-defined]
    success = True
    image = None
    retval: np.ndarray | tuple[np.ndarray, PNGHeader] | None = None
    try:
        with open(filename, "rb") as in_file:
            raw_file = in_file.read()
        image = cv2.imdecode(np.frombuffer(raw_file, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Image is None")
        if image.ndim == 2:  # Convert grayscale to BGR
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 2 and image.shape[2] == 4:  # Strip mask
            image = image[:, :, :3]

        if np.issubdtype(image.dtype, np.integer):
            info = np.iinfo(T.cast(np.integer, image.dtype))  # Scale non UINT8 INT images to UINT8
            if info.max != 255:
                image = image.astype(np.float32) / info.max * 255.0
        elif np.issubdtype(image.dtype, np.floating):
            # Just naively clip floating images to 0-1 for now
            image = (np.clip(image, 0.0, 1.0) * 255.).astype(np.float32)

        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)

        if with_metadata:
            metadata = png_read_meta(raw_file)
            assert isinstance(metadata, PNGHeader)
            retval = (image, metadata)
        else:
            retval = image
    except TypeError as err:
        success = False
        msg = f"Error while reading image (TypeError): '{filename}'"
        msg += f". Original error message: {str(err)}"
        logger.error(msg)
        if raise_error:
            raise TypeError(msg) from err
    except ValueError as err:
        success = False
        msg = ("Error while reading image. This can be caused by special characters in the "
               f"filename or a corrupt image file: '{filename}'")
        msg += f". Original error message: {str(err)}"
        logger.error(msg)
        if raise_error:
            raise ValueError(msg) from err
    except Exception as err:  # pylint:disable=broad-except
        success = False
        msg = f"Failed to load image '{filename}'. Original Error: {str(err)}"
        logger.error(msg)
        if raise_error:
            raise Exception(msg) from err  # pylint:disable=broad-exception-raised
    logger.trace("Loaded image: '%s'. Success: %s", filename, success)  # type:ignore[attr-defined]
    return retval