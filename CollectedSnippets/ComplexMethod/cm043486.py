def check_file(file, suffix=""):
    """Searches/downloads a file, checks its suffix (if provided), and returns the file path."""
    check_suffix(file, suffix)  # optional
    file = str(file)  # convert to str()
    if os.path.isfile(file) or not file:  # exists
        return file
    elif file.startswith(("http:/", "https:/")):  # download
        url = file  # warning: Pathlib turns :// -> :/
        file = Path(urllib.parse.unquote(file).split("?")[0]).name  # '%2F' to '/', split https://url.com/file.txt?auth
        if os.path.isfile(file):
            LOGGER.info(f"Found {url} locally at {file}")  # file already exists
        else:
            LOGGER.info(f"Downloading {url} to {file}...")
            torch.hub.download_url_to_file(url, file)
            assert Path(file).exists() and Path(file).stat().st_size > 0, f"File download failed: {url}"  # check
        return file
    elif file.startswith("clearml://"):  # ClearML Dataset ID
        assert "clearml" in sys.modules, (
            "ClearML is not installed, so cannot use ClearML dataset. Try running 'pip install clearml'."
        )
        return file
    else:  # search
        files = []
        for d in "data", "models", "utils":  # search directories
            files.extend(glob.glob(str(ROOT / d / "**" / file), recursive=True))  # find file
        assert len(files), f"File not found: {file}"  # assert file was found
        assert len(files) == 1, f"Multiple files match '{file}', specify exact path: {files}"  # assert unique
        return files[0]