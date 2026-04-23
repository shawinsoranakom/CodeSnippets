def check_dataset(data, autodownload=True):
    """Validates and/or auto-downloads a dataset, returning its configuration as a dictionary."""
    # Download (optional)
    extract_dir = ""
    if isinstance(data, (str, Path)) and (is_zipfile(data) or is_tarfile(data)):
        download(data, dir=f"{DATASETS_DIR}/{Path(data).stem}", unzip=True, delete=False, curl=False, threads=1)
        data = next((DATASETS_DIR / Path(data).stem).rglob("*.yaml"))
        extract_dir, autodownload = data.parent, False

    # Read yaml (optional)
    if isinstance(data, (str, Path)):
        data = yaml_load(data)  # dictionary

    # Checks
    for k in "train", "val", "names":
        assert k in data, emojis(f"data.yaml '{k}:' field missing ❌")
    if isinstance(data["names"], (list, tuple)):  # old array format
        data["names"] = dict(enumerate(data["names"]))  # convert to dict
    assert all(isinstance(k, int) for k in data["names"].keys()), "data.yaml names keys must be integers, i.e. 2: car"
    data["nc"] = len(data["names"])

    # Resolve paths
    path = Path(extract_dir or data.get("path") or "")  # optional 'path' default to '.'
    if not path.is_absolute():
        path = (ROOT / path).resolve()
        data["path"] = path  # download scripts
    for k in "train", "val", "test":
        if data.get(k):  # prepend path
            if isinstance(data[k], str):
                x = (path / data[k]).resolve()
                if not x.exists() and data[k].startswith("../"):
                    x = (path / data[k][3:]).resolve()
                data[k] = str(x)
            else:
                data[k] = [str((path / x).resolve()) for x in data[k]]

    # Parse yaml
    _train, val, _test, s = (data.get(x) for x in ("train", "val", "test", "download"))
    if val:
        val = [Path(x).resolve() for x in (val if isinstance(val, list) else [val])]  # val path
        if not all(x.exists() for x in val):
            LOGGER.info("\nDataset not found ⚠️, missing paths %s" % [str(x) for x in val if not x.exists()])
            if not s or not autodownload:
                raise Exception("Dataset not found ❌")
            t = time.time()
            if s.startswith("http") and s.endswith(".zip"):  # URL
                f = Path(s).name  # filename
                LOGGER.info(f"Downloading {s} to {f}...")
                torch.hub.download_url_to_file(s, f)
                Path(DATASETS_DIR).mkdir(parents=True, exist_ok=True)  # create root
                unzip_file(f, path=DATASETS_DIR)  # unzip
                Path(f).unlink()  # remove zip
                r = None  # success
            elif s.startswith("bash "):  # bash script
                LOGGER.info(f"Running {s} ...")
                r = subprocess.run(s, shell=True)
            else:  # python script
                r = exec(s, {"yaml": data})  # return None
            dt = f"({round(time.time() - t, 1)}s)"
            s = f"success ✅ {dt}, saved to {colorstr('bold', DATASETS_DIR)}" if r in (0, None) else f"failure {dt} ❌"
            LOGGER.info(f"Dataset download {s}")
    check_font("Arial.ttf" if is_ascii(data["names"]) else "Arial.Unicode.ttf", progress=True)  # download fonts
    return data