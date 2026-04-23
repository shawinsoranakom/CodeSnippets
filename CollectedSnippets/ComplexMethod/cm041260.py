def download(
    url: str,
    path: str,
    verify_ssl: bool = True,
    timeout: float = None,
    request_headers: dict | None = None,
    quiet: bool = False,
) -> None:
    """Downloads file at url to the given path. Raises TimeoutError if the optional timeout (in secs) is reached.

    If `quiet` is passed, do not log any status messages. Error messages are still logged.
    """

    # make sure we're creating a new session here to enable parallel file downloads
    s = requests.Session()
    proxies = get_proxies()
    if proxies:
        s.proxies.update(proxies)

    # Use REQUESTS_CA_BUNDLE path. If it doesn't exist, use the method provided settings.
    # Note that a value that is not False, will result to True and will get the bundle file.
    _verify = os.getenv("REQUESTS_CA_BUNDLE", verify_ssl)

    r = None
    try:
        r = s.get(url, stream=True, verify=_verify, timeout=timeout, headers=request_headers)
        # check status code before attempting to read body
        if not r.ok:
            raise Exception(f"Failed to download {url}, response code {r.status_code}")

        total_size = 0
        if r.headers.get("Content-Length"):
            total_size = int(r.headers.get("Content-Length"))

        total_downloaded = 0
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        if not quiet:
            LOG.debug("Starting download from %s to %s", url, path)
        with open(path, "wb") as f:
            iter_length = 0
            percentage_limit = next_percentage_record = 10  # print a log line for every 10%
            iter_limit = (
                1000000  # if we can't tell the percentage, print a log line for every 1MB chunk
            )
            for chunk in r.iter_content(DOWNLOAD_CHUNK_SIZE):
                # explicitly check the raw stream, since the size from the chunk can be bigger than the amount of
                # bytes transferred over the wire due to transparent decompression (f.e. GZIP)
                new_total_downloaded = r.raw.tell()
                iter_length += new_total_downloaded - total_downloaded
                total_downloaded = new_total_downloaded
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                elif not quiet:
                    LOG.debug(
                        "Empty chunk %s (total %dK of %dK) from %s",
                        chunk,
                        total_downloaded / 1024,
                        total_size / 1024,
                        url,
                    )

                if total_size > 0 and (
                    (current_percent := total_downloaded / total_size * 100)
                    >= next_percentage_record
                ):
                    # increment the limit for the next log output (ensure that there is max 1 log message per block)
                    # f.e. percentage_limit is 10, current percentage is 71: next log is earliest at 80%
                    next_percentage_record = (
                        math.floor(current_percent / percentage_limit) * percentage_limit
                        + percentage_limit
                    )
                    if not quiet:
                        LOG.debug(
                            "Downloaded %d%% (total %dK of %dK) to %s",
                            current_percent,
                            total_downloaded / 1024,
                            total_size / 1024,
                            path,
                        )
                    iter_length = 0
                elif total_size <= 0 and iter_length >= iter_limit:
                    if not quiet:
                        # print log message every x K if the total size is not known
                        LOG.debug(
                            "Downloaded %dK (total %dK) to %s",
                            iter_length / 1024,
                            total_downloaded / 1024,
                            path,
                        )
                    iter_length = 0
            f.flush()
            os.fsync(f)
        if os.path.getsize(path) == 0:
            LOG.warning("Zero bytes downloaded from %s, retrying", url)
            download(url, path, verify_ssl)
            return
        if not quiet:
            LOG.debug(
                "Done downloading %s, response code %s, total %dK",
                url,
                r.status_code,
                total_downloaded / 1024,
            )
    except requests.exceptions.ReadTimeout as e:
        raise TimeoutError(f"Timeout ({timeout}) reached on download: {url} - {e}")
    finally:
        if r is not None:
            r.close()
        s.close()