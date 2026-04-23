def copy_py39_to_py310() -> None:
    """
    For each docs_src file/directory with a _py39 label that has no _py310
    counterpart, copy it with the _py310 label.
    """
    docs_src_path = Path("docs_src")
    # Handle directory-level labels (e.g. app_b_an_py39/)
    for dir_path in sorted(docs_src_path.rglob("*_py39")):
        if not dir_path.is_dir():
            continue
        py310_dir = dir_path.parent / dir_path.name.replace("_py39", "_py310")
        if py310_dir.exists():
            continue
        logging.info(f"Copying directory {dir_path} -> {py310_dir}")
        shutil.copytree(dir_path, py310_dir)
    # Handle file-level labels (e.g. tutorial001_py39.py)
    for file_path in sorted(docs_src_path.rglob("*_py39.py")):
        if not file_path.is_file():
            continue
        # Skip files inside _py39 directories (already handled above)
        if "_py39" in file_path.parent.name:
            continue
        py310_file = file_path.with_name(
            file_path.name.replace("_py39.py", "_py310.py")
        )
        if py310_file.exists():
            continue
        logging.info(f"Copying file {file_path} -> {py310_file}")
        shutil.copy2(file_path, py310_file)