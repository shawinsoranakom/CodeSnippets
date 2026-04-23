def create_zip_file(
    file_path: str,
    zip_file: str = None,
    get_content: bool = False,
    content_root: str = None,
    mode: Literal["r", "w", "x", "a"] = "w",
):
    """
    Creates a zipfile to the designated file_path.

    By default, a new zip file is created but the mode parameter can be used to append to an existing zip file
    """
    base_dir = file_path
    if not os.path.isdir(file_path):
        base_dir = tempfile.mkdtemp(prefix=ARCHIVE_DIR_PREFIX)
        shutil.copy(file_path, base_dir)
        TMP_FILES.append(base_dir)
    tmp_dir = tempfile.mkdtemp(prefix=ARCHIVE_DIR_PREFIX)
    full_zip_file = zip_file
    if not full_zip_file:
        zip_file_name = "archive.zip"
        full_zip_file = os.path.join(tmp_dir, zip_file_name)
    # special case where target folder is empty -> create empty zip file
    if is_empty_dir(base_dir):
        # see https://stackoverflow.com/questions/25195495/how-to-create-an-empty-zip-file#25195628
        content = (
            b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )
        if get_content:
            return content
        save_file(full_zip_file, content)
        return full_zip_file

    # TODO: using a different packaging method here also produces wildly different .zip package sizes
    if is_debian() and "PYTEST_CURRENT_TEST" not in os.environ:
        # todo: extend CLI with the new parameters
        create_zip_file_cli(source_path=file_path, base_dir=base_dir, zip_file=full_zip_file)
    else:
        create_zip_file_python(
            base_dir=base_dir, zip_file=full_zip_file, mode=mode, content_root=content_root
        )
    if not get_content:
        TMP_FILES.append(tmp_dir)
        return full_zip_file
    with open(full_zip_file, "rb") as file_obj:
        zip_file_content = file_obj.read()
    rm_rf(tmp_dir)
    return zip_file_content