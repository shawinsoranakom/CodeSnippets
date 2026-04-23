def download_and_extract(
    archive_url: str,
    target_dir: str,
    retries: int | None = 0,
    sleep: int | None = 3,
    tmp_archive: str | None = None,
    checksum_url: str | None = None,
) -> None:
    """
    Download and extract an archive to a target directory with optional checksum verification.

    Checksum verification is only performed if a `checksum_url` is provided.
    Else, the archive is downloaded and extracted without verification.

    :param archive_url: URL of the archive to download
    :param target_dir: Directory to extract the archive contents to
    :param retries: Number of download retries (default: 0)
    :param sleep: Sleep time between retries in seconds (default: 3)
    :param tmp_archive: Optional path for the temporary archive file
    :param checksum_url: Optional URL of the checksum file for verification
    :return: None
    """
    mkdir(target_dir)

    _, ext = os.path.splitext(tmp_archive or archive_url)
    tmp_archive = tmp_archive or new_tmp_file()
    if not os.path.exists(tmp_archive) or os.path.getsize(tmp_archive) <= 0:
        # create temporary placeholder file, to avoid duplicate parallel downloads
        save_file(tmp_archive, "")

        for i in range(retries + 1):
            try:
                download(archive_url, tmp_archive)
                break
            except Exception as e:
                LOG.warning(
                    "Attempt %d. Failed to download archive from %s: %s",
                    i + 1,
                    archive_url,
                    e,
                )
                # only sleep between retries, not after the last one
                if i < retries:
                    time.sleep(sleep)

    # if the temporary file we created above hasn't been replaced, we assume failure
    if os.path.getsize(tmp_archive) <= 0:
        raise Exception("Failed to download archive from %s: . Retries exhausted", archive_url)

    # Verify checksum if provided
    if checksum_url:
        LOG.info("Verifying archive integrity...")
        try:
            verify_local_file_with_checksum_url(
                file_path=tmp_archive,
                checksum_url=checksum_url,
            )
        except Exception as e:
            # clean up the corrupted download
            rm_rf(tmp_archive)
            raise e

    if ext in (".zip", ".whl"):
        unzip(tmp_archive, target_dir)
    elif ext in (
        ".bz2",
        ".gz",
        ".tgz",
        ".xz",
    ):
        untar(tmp_archive, target_dir)
    else:
        raise Exception(f"Unsupported archive format: {ext}")