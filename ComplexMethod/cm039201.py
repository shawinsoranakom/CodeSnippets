def _fetch_remote(remote, dirname=None, n_retries=3, delay=1):
    """Helper function to download a remote dataset.

    Fetch a dataset pointed by remote's url, save into path using remote's
    filename and ensure its integrity based on the SHA256 checksum of the
    downloaded file.

    .. versionchanged:: 1.6

        If the file already exists locally and the SHA256 checksums match, the
        path to the local file is returned without re-downloading.

    Parameters
    ----------
    remote : RemoteFileMetadata
        Named tuple containing remote dataset meta information: url, filename
        and checksum.

    dirname : str or Path, default=None
        Directory to save the file to. If None, the current working directory
        is used.

    n_retries : int, default=3
        Number of retries when HTTP errors are encountered.

        .. versionadded:: 1.5

    delay : int, default=1
        Number of seconds between retries.

        .. versionadded:: 1.5

    Returns
    -------
    file_path: Path
        Full path of the created file.
    """
    if dirname is None:
        folder_path = Path(".")
    else:
        folder_path = Path(dirname)

    file_path = folder_path / remote.filename

    if file_path.exists():
        if remote.checksum is None:
            return file_path

        checksum = _sha256(file_path)
        if checksum == remote.checksum:
            return file_path
        else:
            warnings.warn(
                f"SHA256 checksum of existing local file {file_path.name} "
                f"({checksum}) differs from expected ({remote.checksum}): "
                f"re-downloading from {remote.url} ."
            )

    # We create a temporary file dedicated to this particular download to avoid
    # conflicts with parallel downloads. If the download is successful, the
    # temporary file is atomically renamed to the final file path (with
    # `shutil.move`). We therefore pass `delete=False` to `NamedTemporaryFile`.
    # Otherwise, garbage collecting temp_file would raise an error when
    # attempting to delete a file that was already renamed. If the download
    # fails or the result does not match the expected SHA256 digest, the
    # temporary file is removed manually in the except block.
    temp_file = NamedTemporaryFile(
        prefix=remote.filename + ".part_", dir=folder_path, delete=False
    )
    # Note that Python 3.12's `delete_on_close=True` is ignored as we set
    # `delete=False` explicitly. So after this line the empty temporary file still
    # exists on disk to make sure that it's uniquely reserved for this specific call of
    # `_fetch_remote` and therefore it protects against any corruption by parallel
    # calls.
    temp_file.close()
    try:
        temp_file_path = Path(temp_file.name)
        while True:
            try:
                urlretrieve(remote.url, temp_file_path)
                break
            except (URLError, TimeoutError):
                if n_retries == 0:
                    # If no more retries are left, re-raise the caught exception.
                    raise
                warnings.warn(f"Retry downloading from url: {remote.url}")
                n_retries -= 1
                time.sleep(delay)

        checksum = _sha256(temp_file_path)
        if remote.checksum is not None and remote.checksum != checksum:
            raise OSError(
                f"The SHA256 checksum of {remote.filename} ({checksum}) "
                f"differs from expected ({remote.checksum})."
            )
    except (Exception, KeyboardInterrupt):
        os.unlink(temp_file.name)
        raise

    # The following renaming is atomic whenever temp_file_path and
    # file_path are on the same filesystem. This should be the case most of
    # the time, but we still use shutil.move instead of os.rename in case
    # they are not.
    shutil.move(temp_file_path, file_path)

    return file_path