def zip_directory(
    directory: str | Path,
    compress: bool = True,
    exclude: tuple[str, ...] = (".DS_Store", "__MACOSX"),
    progress: bool = True,
) -> Path:
    """Zip the contents of a directory, excluding specified files.

    The resulting zip file is named after the directory and placed alongside it.

    Args:
        directory (str | Path): The path to the directory to be zipped.
        compress (bool): Whether to compress the files while zipping.
        exclude (tuple[str, ...], optional): A tuple of filename strings to be excluded.
        progress (bool, optional): Whether to display a progress bar.

    Returns:
        (Path): The path to the resulting zip file.

    Examples:
        >>> from ultralytics.utils.downloads import zip_directory
        >>> file = zip_directory("path/to/dir")
    """
    from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

    delete_dsstore(directory)
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")

    # Zip with progress bar
    files = [f for f in directory.rglob("*") if f.is_file() and all(x not in f.name for x in exclude)]  # files to zip
    zip_file = directory.with_suffix(".zip")
    compression = ZIP_DEFLATED if compress else ZIP_STORED
    with ZipFile(zip_file, "w", compression) as f:
        for file in TQDM(files, desc=f"Zipping {directory} to {zip_file}...", unit="files", disable=not progress):
            f.write(file, file.relative_to(directory))

    return zip_file