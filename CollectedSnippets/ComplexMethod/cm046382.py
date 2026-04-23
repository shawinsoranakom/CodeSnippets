def check_file(file, suffix="", download=True, download_dir=".", hard=True):
    """Search/download file (if necessary), check suffix (if provided), and return path.

    Args:
        file (str): File name or path, URL, platform URI (ul://), or GCS path (gs://).
        suffix (str | tuple): Acceptable suffix or tuple of suffixes to validate against the file.
        download (bool): Whether to download the file if it doesn't exist locally.
        download_dir (str): Directory to download the file to.
        hard (bool): Whether to raise an error if the file is not found.

    Returns:
        (str | list): Path to the file, or an empty list if not found.
    """
    check_suffix(file, suffix)  # optional
    file = str(file).strip()  # convert to string and strip spaces
    file = check_yolov5u_filename(file)  # yolov5n -> yolov5nu
    if (
        not file
        or ("://" not in file and Path(file).exists())  # '://' check required in Windows Python<3.10
        or file.lower().startswith("grpc://")
    ):  # file exists or gRPC Triton images
        return file
    elif download and file.lower().startswith("ul://"):  # Ultralytics Platform URI
        from ultralytics.utils.callbacks.platform import resolve_platform_uri

        url = resolve_platform_uri(file, hard=hard)  # Convert to signed HTTPS URL
        if url is None:
            return []  # Not found, soft fail (consistent with file search behavior)
        # Use URI path for unique directory structure: ul://user/project/model -> user/project/model/filename.pt
        uri_path = file[5:]  # Remove "ul://"
        local_file = Path(download_dir) / uri_path / url2file(url)
        # Always re-download NDJSON datasets (cheap, ensures fresh data after updates)
        if local_file.suffix == ".ndjson":
            local_file.unlink(missing_ok=True)
        if local_file.exists():
            LOGGER.info(f"Found {clean_url(url)} locally at {local_file}")
        else:
            local_file.parent.mkdir(parents=True, exist_ok=True)
            downloads.safe_download(url=url, file=local_file, unzip=False)
        return str(local_file)
    elif download and file.lower().startswith(
        ("https://", "http://", "rtsp://", "rtmp://", "tcp://", "gs://")
    ):  # download
        if file.startswith("gs://"):
            file = "https://storage.googleapis.com/" + file[5:]  # convert gs:// to public HTTPS URL
        url = file  # warning: Pathlib turns :// -> :/
        file = Path(download_dir) / url2file(file)  # '%2F' to '/', split https://url.com/file.txt?auth
        if file.exists():
            LOGGER.info(f"Found {clean_url(url)} locally at {file}")  # file already exists
        else:
            downloads.safe_download(url=url, file=file, unzip=False)
        return str(file)
    else:  # search
        files = glob.glob(str(ROOT / "**" / file), recursive=True) or glob.glob(str(ROOT.parent / file))  # find file
        if not files and hard:
            raise FileNotFoundError(f"'{file}' does not exist")
        elif len(files) > 1 and hard:
            raise FileNotFoundError(f"Multiple files match '{file}', specify exact path: {files}")
        return files[0] if len(files) else []