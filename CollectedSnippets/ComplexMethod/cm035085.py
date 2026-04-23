def _download(url, save_path):
    """
    Download from url, save to path.

    url (str): download url
    save_path (str): download to given path
    """
    logger = get_logger()

    fname = osp.split(url)[-1]
    retry_cnt = 0

    while not osp.exists(save_path):
        if retry_cnt < DOWNLOAD_RETRY_LIMIT:
            retry_cnt += 1
        else:
            raise RuntimeError(
                "Download from {} failed. " "Retry limit reached".format(url)
            )

        try:
            req = requests.get(url, stream=True)
        except Exception as e:  # requests.exceptions.ConnectionError
            logger.info(
                "Downloading {} from {} failed {} times with exception {}".format(
                    fname, url, retry_cnt + 1, str(e)
                )
            )
            time.sleep(1)
            continue

        if req.status_code != 200:
            raise RuntimeError(
                "Downloading from {} failed with code "
                "{}!".format(url, req.status_code)
            )

        # For protecting download interrupted, download to
        # tmp_file firstly, move tmp_file to save_path
        # after download finished
        tmp_file = save_path + ".tmp"
        total_size = req.headers.get("content-length")
        with open(tmp_file, "wb") as f:
            if total_size:
                with tqdm(total=(int(total_size) + 1023) // 1024) as pbar:
                    for chunk in req.iter_content(chunk_size=1024):
                        f.write(chunk)
                        pbar.update(1)
            else:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        shutil.move(tmp_file, save_path)

    return save_path