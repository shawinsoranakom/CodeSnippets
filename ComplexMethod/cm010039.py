def download_url_to_file(
    url: str,
    dst: str,
    hash_prefix: str | None = None,
    progress: bool = True,
) -> None:
    r"""Download object at the given URL to a local path.

    Args:
        url (str): URL of the object to download
        dst (str): Full path where object will be saved, e.g. ``/tmp/temporary_file``
        hash_prefix (str, optional): If not None, the SHA256 downloaded file should start with ``hash_prefix``.
            Default: None
        progress (bool, optional): whether or not to display a progress bar to stderr
            Default: True

    Example:
        >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_HUB)
        >>> # xdoctest: +REQUIRES(POSIX)
        >>> torch.hub.download_url_to_file(
        ...     "https://s3.amazonaws.com/pytorch/models/resnet18-5c106cde.pth",
        ...     "/tmp/temporary_file",
        ... )

    """
    # We deliberately save it in a temp file and move it after
    # download is complete. This prevents a local working checkpoint
    # being overridden by a broken download.
    # We deliberately do not use NamedTemporaryFile to avoid restrictive
    # file permissions being applied to the downloaded file.
    dst = os.path.expanduser(dst)
    for _ in range(tempfile.TMP_MAX):
        tmp_dst = dst + "." + uuid.uuid4().hex + ".partial"
        try:
            f = open(tmp_dst, "w+b")  # noqa: SIM115
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError(errno.EEXIST, "No usable temporary file name found")
    req = Request(url, headers={"User-Agent": "torch.hub"})
    try:
        with urlopen(req) as u:
            meta = u.info()
            if hasattr(meta, "getheaders"):
                content_length = meta.getheaders("Content-Length")
            else:
                content_length = meta.get_all("Content-Length")
            file_size = None
            if content_length is not None and len(content_length) > 0:
                file_size = int(content_length[0])

            sha256 = hashlib.sha256() if hash_prefix is not None else None
            with tqdm(
                total=file_size,
                disable=not progress,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                while True:
                    buffer = u.read(READ_DATA_CHUNK)
                    if len(buffer) == 0:
                        break
                    f.write(buffer)
                    if sha256 is not None:
                        sha256.update(buffer)
                    pbar.update(len(buffer))

            f.close()
            if sha256 is not None and hash_prefix is not None:
                digest = sha256.hexdigest()
                if digest[: len(hash_prefix)] != hash_prefix:
                    raise RuntimeError(
                        f'invalid hash value (expected "{hash_prefix}", got "{digest}")'
                    )
        shutil.move(f.name, dst)
    finally:
        f.close()
        if os.path.exists(f.name):
            os.remove(f.name)