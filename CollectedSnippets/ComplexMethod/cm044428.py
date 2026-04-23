def read_image_batch(filenames: list[str], with_metadata: bool = False
                     ) -> np.ndarray | tuple[np.ndarray, list[PNGHeader]]:
    """Load a batch of images from the given file locations.

    Leverages multi-threading to load multiple images from disk at the same time leading to vastly
    reduced image read times.

    Parameters
    ----------
    filenames
        A of full paths to the images to be loaded.
    with_metadata
        Only returns a value if the images loaded are extracted Faceswap faces. If ``True`` then
        returns the Faceswap metadata stored within each Face's .png exif header.
        Default: ``False``

    Returns
    -------
    batch
        The batch of images in `BGR` channel order returned in the order of :attr:`filenames`
    metadata
        The faceswap metadata corresponding to each image in the batch. Only returned if
        `with_metadata` is ``True``

    Notes
    -----
    As the images are compiled into a batch, they should be all of the same dimensions, otherwise a
    homogenous array will be returned

    Example
    -------
    >>> image_filenames = ["/path/to/image_1.png", "/path/to/image_2.png", "/path/to/image_3.png"]
    >>> images = read_image_batch(image_filenames)
    >>> print(images.shape)
    ... (3, 64, 64, 3)
    >>> images, metadata = read_image_batch(image_filenames, with_metadata=True)
    >>> print(images.shape)
    ... (3, 64, 64, 3)
    >>> print(len(metadata))
    ... 3
    """
    logger.trace("Requested batch: '%s'", filenames)  # type:ignore[attr-defined]
    batch: list[np.ndarray | None] = [None for _ in range(len(filenames))]
    meta: list[PNGHeader | None] = [None for _ in range(len(filenames))]

    with futures.ThreadPoolExecutor() as executor:
        images = {executor.submit(  # NOTE submit strips positionals, breaking type-checking
                    read_image,  # type:ignore[arg-type]
                    filename,
                    raise_error=True,  # pyright:ignore[reportArgumentType]
                    with_metadata=with_metadata): idx  # pyright:ignore[reportArgumentType]
                  for idx, filename in enumerate(filenames)}

        for future in futures.as_completed(images):
            result = T.cast(np.ndarray | tuple[np.ndarray, "PNGHeader"], future.result())
            ret_idx = images[future]
            if with_metadata:
                assert isinstance(result, tuple)
                batch[ret_idx], meta[ret_idx] = result
            else:
                assert isinstance(result, np.ndarray)
                batch[ret_idx] = result

    arr_batch = np.array(batch)
    retval: np.ndarray | tuple[np.ndarray, list[PNGHeader]]
    if with_metadata:
        retval = (arr_batch, T.cast(list["PNGHeader"], meta))
    else:
        retval = arr_batch

    logger.trace(  # type:ignore[attr-defined]
        "Returning images: (filenames: %s, batch shape: %s, with_metadata: %s)",
        filenames, arr_batch.shape, with_metadata)
    return retval