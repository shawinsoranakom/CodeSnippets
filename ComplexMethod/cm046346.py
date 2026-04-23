def safe_download(
    url: str | Path,
    file: str | Path | None = None,
    dir: str | Path | None = None,
    unzip: bool = True,
    delete: bool = False,
    curl: bool = False,
    retry: int = 3,
    min_bytes: float = 1e0,
    exist_ok: bool = False,
    progress: bool = True,
) -> Path | str:
    """Download files from a URL with options for retrying, unzipping, and deleting the downloaded file. Enhanced with
    robust partial download detection using Content-Length validation.

    Args:
        url (str | Path): The URL of the file to be downloaded.
        file (str | Path, optional): The filename of the downloaded file. If not provided, the file will be saved with
            the same name as the URL.
        dir (str | Path, optional): The directory to save the downloaded file. If not provided, the file will be saved
            in the current working directory.
        unzip (bool, optional): Whether to unzip the downloaded file.
        delete (bool, optional): Whether to delete the downloaded file after unzipping.
        curl (bool, optional): Whether to use curl command line tool for downloading.
        retry (int, optional): The number of times to retry the download in case of failure.
        min_bytes (float, optional): The minimum number of bytes that the downloaded file should have, to be considered
            a successful download.
        exist_ok (bool, optional): Whether to overwrite existing contents during unzipping.
        progress (bool, optional): Whether to display a progress bar during the download.

    Returns:
        (Path | str): The path to the downloaded file or extracted directory.

    Examples:
        >>> from ultralytics.utils.downloads import safe_download
        >>> link = "https://ultralytics.com/assets/bus.jpg"
        >>> path = safe_download(link)
    """
    url = str(url)
    if "://" not in url and Path(url).is_file():  # local file path ('://' check required in Windows Python<3.10)
        f = Path(url)
    else:
        gdrive = url.startswith("https://drive.google.com/")  # check if the URL is a Google Drive link
        if gdrive:
            url, file = get_google_drive_file_info(url)
        url = url.replace(" ", "%20")  # encode spaces for curl/urllib compatibility

        f = Path(dir or ".") / (file or url2file(url))  # URL converted to filename
        if not f.is_file():  # URL and file do not exist
            uri = (url if gdrive else clean_url(url)).replace(ASSETS_URL, "https://ultralytics.com/assets")  # clean
            desc = f"Downloading {uri} to '{f}'"
            f.parent.mkdir(parents=True, exist_ok=True)  # make directory if missing
            curl_installed = shutil.which("curl")
            for i in range(retry + 1):
                try:
                    if (curl or i > 0) and curl_installed:  # curl download with retry, continue
                        s = "sS" * (not progress)  # silent
                        r = subprocess.run(["curl", "-#", f"-{s}L", url, "-o", f, "--retry", "3", "-C", "-"]).returncode
                        assert r == 0, f"Curl return value {r}"
                        expected_size = None  # Can't get size with curl
                    else:  # urllib download
                        with request.urlopen(url) as response:
                            expected_size = int(response.getheader("Content-Length", 0))
                            if i == 0 and expected_size > 1048576:
                                check_disk_space(expected_size, path=f.parent)
                            buffer_size = max(8192, min(1048576, expected_size // 1000)) if expected_size else 8192
                            with TQDM(
                                total=expected_size,
                                desc=desc,
                                disable=not progress,
                                unit="B",
                                unit_scale=True,
                                unit_divisor=1024,
                            ) as pbar:
                                with open(f, "wb") as f_opened:
                                    while True:
                                        data = response.read(buffer_size)
                                        if not data:
                                            break
                                        f_opened.write(data)
                                        pbar.update(len(data))

                    if f.exists():
                        file_size = f.stat().st_size
                        if file_size > min_bytes:
                            # Check if download is complete (only if we have expected_size)
                            if expected_size and file_size != expected_size:
                                LOGGER.warning(
                                    f"Partial download: {file_size}/{expected_size} bytes ({file_size / expected_size * 100:.1f}%)"
                                )
                            else:
                                break  # success
                        f.unlink()  # remove partial downloads
                except MemoryError:
                    raise  # Re-raise immediately - no point retrying if insufficient disk space
                except Exception as e:
                    if i == 0 and not is_online():
                        raise ConnectionError(
                            emojis(f"❌  Download failure for {uri}. Environment may be offline.")
                        ) from e
                    elif i >= retry:
                        raise ConnectionError(
                            emojis(f"❌  Download failure for {uri}. Retry limit reached. {e}")
                        ) from e
                    LOGGER.warning(f"Download failure, retrying {i + 1}/{retry} {uri}... {e}")

    if unzip and f.exists() and f.suffix in {"", ".zip", ".tar", ".gz"}:
        from zipfile import is_zipfile

        unzip_dir = (dir or f.parent).resolve()  # unzip to dir if provided else unzip in place
        if is_zipfile(f):
            unzip_dir = unzip_file(file=f, path=unzip_dir, exist_ok=exist_ok, progress=progress)  # unzip
        elif f.suffix in {".tar", ".gz"}:
            LOGGER.info(f"Unzipping {f} to {unzip_dir}...")
            subprocess.run(["tar", "xf" if f.suffix == ".tar" else "xfz", f, "--directory", unzip_dir], check=True)
        if delete:
            f.unlink()  # remove zip
        return unzip_dir
    return f