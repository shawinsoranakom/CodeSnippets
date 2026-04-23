def unzip_file(
    file: str | Path,
    path: str | Path | None = None,
    exclude: tuple[str, ...] = (".DS_Store", "__MACOSX"),
    exist_ok: bool = False,
    progress: bool = True,
) -> Path:
    """Unzip a *.zip file to the specified path, excluding specified files.

    If the zipfile does not contain a single top-level directory, the function will create a new directory with the same
    name as the zipfile (without the extension) to extract its contents. If a path is not provided, the function will
    use the parent directory of the zipfile as the default path.

    Args:
        file (str | Path): The path to the zipfile to be extracted.
        path (str | Path, optional): The path to extract the zipfile to.
        exclude (tuple[str, ...], optional): A tuple of filename strings to be excluded.
        exist_ok (bool, optional): Whether to overwrite existing contents if they exist.
        progress (bool, optional): Whether to display a progress bar.

    Returns:
        (Path): The path to the directory where the zipfile was extracted.

    Raises:
        BadZipFile: If the provided file does not exist or is not a valid zipfile.

    Examples:
        >>> from ultralytics.utils.downloads import unzip_file
        >>> directory = unzip_file("path/to/file.zip")
    """
    from zipfile import BadZipFile, ZipFile, is_zipfile

    if not (Path(file).exists() and is_zipfile(file)):
        raise BadZipFile(f"File '{file}' does not exist or is a bad zip file.")
    if path is None:
        path = Path(file).parent  # default path

    # Unzip the file contents
    with ZipFile(file) as zipObj:
        files = [f for f in zipObj.namelist() if all(x not in f for x in exclude)]
        top_level_dirs = {Path(f).parts[0] for f in files}

        # Decide to unzip directly or unzip into a directory
        unzip_as_dir = len(top_level_dirs) == 1  # (len(files) > 1 and not files[0].endswith("/"))
        if unzip_as_dir:
            # Zip has 1 top-level directory
            extract_path = path  # i.e. ../datasets
            path = Path(path) / next(iter(top_level_dirs))  # i.e. extract coco8/ dir to ../datasets/
        else:
            # Zip has multiple files at top level
            path = extract_path = Path(path) / Path(file).stem  # i.e. extract multiple files to ../datasets/coco8/

        # Check if destination directory already exists and contains files
        if path.exists() and any(path.iterdir()) and not exist_ok:
            # If it exists and is not empty, return the path without unzipping
            LOGGER.warning(f"Skipping {file} unzip as destination directory {path} is not empty.")
            return path

        for f in TQDM(files, desc=f"Unzipping {file} to {Path(path).resolve()}...", unit="files", disable=not progress):
            # Ensure the file is within the extract_path to avoid path traversal security vulnerability
            if ".." in Path(f).parts:
                LOGGER.warning(f"Potentially insecure file path: {f}, skipping extraction.")
                continue
            zipObj.extract(f, extract_path)

    return path