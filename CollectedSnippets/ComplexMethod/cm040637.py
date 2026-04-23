def get_file(
    fname=None,
    origin=None,
    untar=False,
    md5_hash=None,
    file_hash=None,
    cache_subdir="datasets",
    hash_algorithm="auto",
    extract=False,
    archive_format="auto",
    cache_dir=None,
    force_download=False,
):
    """Downloads a file from a URL if it not already in the cache.

    By default the file at the url `origin` is downloaded to the
    cache_dir `~/.keras`, placed in the cache_subdir `datasets`,
    and given the filename `fname`. The final location of a file
    `example.txt` would therefore be `~/.keras/datasets/example.txt`.
    Files in `.tar`, `.tar.gz`, `.tar.bz`, and `.zip` formats can
    also be extracted.

    Passing a hash will verify the file after download. The command line
    programs `shasum` and `sha256sum` can compute the hash.

    Example:

    ```python
    path_to_downloaded_file = get_file(
        origin="https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz",
        extract=True
    )
    ```

    Args:
        fname: If the target is a single file, this is your desired
            local name for the file.
            If `None`, the name of the file at `origin` will be used.
            If downloading and extracting a directory archive,
            the provided `fname` will be used as extraction directory
            name (only if it doesn't have an extension).
        origin: Original URL of the file.
        untar: Deprecated in favor of `extract` argument.
            Boolean, whether the file is a tar archive that should
            be extracted.
        md5_hash: Deprecated in favor of `file_hash` argument.
            md5 hash of the file for file integrity verification.
        file_hash: The expected hash string of the file after download.
            The sha256 and md5 hash algorithms are both supported.
        cache_subdir: Subdirectory under the Keras cache dir where the file is
            saved. If an absolute path, e.g. `"/path/to/folder"` is
            specified, the file will be saved at that location.
        hash_algorithm: Select the hash algorithm to verify the file.
            options are `"md5'`, `"sha256'`, and `"auto'`.
            The default 'auto' detects the hash algorithm in use.
        extract: If `True`, extracts the archive. Only applicable to compressed
            archive files like tar or zip.
        archive_format: Archive format to try for extracting the file.
            Options are `"auto'`, `"tar'`, `"zip'`, and `None`.
            `"tar"` includes tar, tar.gz, and tar.bz files.
            The default `"auto"` corresponds to `["tar", "zip"]`.
            None or an empty list will return no matches found.
        cache_dir: Location to store cached files, when None it
            defaults ether `$KERAS_HOME` if the `KERAS_HOME` environment
            variable is set or `~/.keras/`.
        force_download: If `True`, the file will always be re-downloaded
            regardless of the cache state.

    Returns:
        Path to the downloaded file.

    **⚠️ Warning on malicious downloads ⚠️**

    Downloading something from the Internet carries a risk.
    NEVER download a file/archive if you do not trust the source.
    We recommend that you specify the `file_hash` argument
    (if the hash of the source file is known) to make sure that the file you
    are getting is the one you expect.
    """
    if origin is None:
        raise ValueError(
            'Please specify the "origin" argument (URL of the file '
            "to download)."
        )

    if cache_dir is None:
        cache_dir = config.keras_home()
    if md5_hash is not None and file_hash is None:
        file_hash = md5_hash
        hash_algorithm = "md5"
    datadir_base = os.path.expanduser(cache_dir)
    if not os.access(datadir_base, os.W_OK):
        datadir_base = os.path.join(
            "/tmp" if os.path.isdir("/tmp") else tempfile.gettempdir(), ".keras"
        )
    datadir = os.path.join(datadir_base, cache_subdir)
    os.makedirs(datadir, exist_ok=True)

    provided_fname = fname
    fname = path_to_string(fname)

    if not fname:
        fname = os.path.basename(urllib.parse.urlsplit(origin).path)
        if not fname:
            raise ValueError(
                "Can't parse the file name from the origin provided: "
                f"'{origin}'."
                "Please specify the `fname` argument."
            )
    else:
        if os.sep in fname:
            raise ValueError(
                "Paths are no longer accepted as the `fname` argument. "
                "To specify the file's parent directory, use "
                f"the `cache_dir` argument. Received: fname={fname}"
            )

    if extract or untar:
        if provided_fname:
            if "." in fname:
                download_target = os.path.join(datadir, fname)
                fname = fname[: fname.find(".")]
                extraction_dir = os.path.join(datadir, f"{fname}_extracted")
            else:
                extraction_dir = os.path.join(datadir, fname)
                download_target = os.path.join(datadir, f"{fname}_archive")
        else:
            extraction_dir = os.path.join(datadir, fname)
            download_target = os.path.join(datadir, f"{fname}_archive")
    else:
        download_target = os.path.join(datadir, fname)

    if force_download:
        download = True
    elif os.path.exists(download_target):
        # File found in cache.
        download = False
        # Verify integrity if a hash was provided.
        if file_hash is not None:
            if not validate_file(
                download_target, file_hash, algorithm=hash_algorithm
            ):
                io_utils.print_msg(
                    "A local file was found, but it seems to be "
                    f"incomplete or outdated because the {hash_algorithm} "
                    "file hash does not match the original value of "
                    f"{file_hash} so we will re-download the data."
                )
                download = True
    else:
        download = True

    if download:
        io_utils.print_msg(f"Downloading data from {origin}")

        class DLProgbar:
            """Manage progress bar state for use in urlretrieve."""

            def __init__(self):
                self.progbar = None
                self.finished = False

            def __call__(self, block_num, block_size, total_size):
                if total_size == -1:
                    total_size = None
                if not self.progbar:
                    self.progbar = Progbar(total_size)
                current = block_num * block_size

                if total_size is None:
                    self.progbar.update(current)
                else:
                    if current < total_size:
                        self.progbar.update(current)
                    elif not self.finished:
                        self.progbar.update(self.progbar.target)
                        self.finished = True

        error_msg = "URL fetch failure on {}: {} -- {}"
        try:
            try:
                urlretrieve(origin, download_target, DLProgbar())
            except urllib.error.HTTPError as e:
                raise Exception(error_msg.format(origin, e.code, e.msg))
            except urllib.error.URLError as e:
                raise Exception(error_msg.format(origin, e.errno, e.reason))
        except (Exception, KeyboardInterrupt):
            if os.path.exists(download_target):
                os.remove(download_target)
            raise

        # Validate download if succeeded and user provided an expected hash
        # Security conscious users would get the hash of the file from a
        # separate channel and pass it to this API to prevent MITM / corruption:
        if os.path.exists(download_target) and file_hash is not None:
            if not validate_file(
                download_target, file_hash, algorithm=hash_algorithm
            ):
                raise ValueError(
                    "Incomplete or corrupted file detected. "
                    f"The {hash_algorithm} "
                    "file hash does not match the provided value "
                    f"of {file_hash}."
                )

    if extract or untar:
        if untar:
            archive_format = "tar"

        status = extract_archive(
            download_target, extraction_dir, archive_format
        )
        if not status:
            warnings.warn("Could not extract archive.", stacklevel=2)
        return extraction_dir

    return download_target