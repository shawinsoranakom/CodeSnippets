def remove_unused_docs_src() -> None:
    """
    Delete .py files in docs_src that are not included in any .md file under docs/.
    """
    docs_src_path = Path("docs_src")
    # Collect all docs .md content referencing docs_src
    all_docs_content = ""
    for md_file in docs_path.rglob("*.md"):
        all_docs_content += md_file.read_text(encoding="utf-8")
    # Build a set of directory-based package roots (e.g. docs_src/bigger_applications/app_py39)
    # where at least one file is referenced in docs. All files in these directories
    # should be kept since they may be internally imported by the referenced files.
    used_package_dirs: set[Path] = set()
    for py_file in docs_src_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = str(py_file)
        if rel_path in all_docs_content:
            # Walk up from the file's parent to find the package root
            # (a subdirectory under docs_src/<topic>/)
            parts = py_file.relative_to(docs_src_path).parts
            if len(parts) > 2:
                # File is inside a sub-package like docs_src/topic/app_xxx/...
                package_root = docs_src_path / parts[0] / parts[1]
                used_package_dirs.add(package_root)
    removed = 0
    for py_file in sorted(docs_src_path.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        # Build the relative path as it appears in includes (e.g. docs_src/first_steps/tutorial001.py)
        rel_path = str(py_file)
        if rel_path in all_docs_content:
            continue
        # If this file is inside a directory-based package where any sibling is
        # referenced, keep it (it's likely imported internally).
        parts = py_file.relative_to(docs_src_path).parts
        if len(parts) > 2:
            package_root = docs_src_path / parts[0] / parts[1]
            if package_root in used_package_dirs:
                continue
        # Check if the _an counterpart (or non-_an counterpart) is referenced.
        # If either variant is included, keep both.
        # Handle both file-level _an (tutorial001_an.py) and directory-level _an
        # (app_an/main.py)
        counterpart_found = False
        full_path_str = str(py_file)
        if "_an" in py_file.stem:
            # This is an _an file, check if the non-_an version is referenced
            counterpart = full_path_str.replace(
                f"/{py_file.stem}", f"/{py_file.stem.replace('_an', '', 1)}"
            )
            if counterpart in all_docs_content:
                counterpart_found = True
        else:
            # This is a non-_an file, check if there's an _an version referenced
            # Insert _an before any version suffix or at the end of the stem
            stem = py_file.stem
            for suffix in ("_py39", "_py310"):
                if suffix in stem:
                    an_stem = stem.replace(suffix, f"_an{suffix}", 1)
                    break
            else:
                an_stem = f"{stem}_an"
            counterpart = full_path_str.replace(f"/{stem}.", f"/{an_stem}.")
            if counterpart in all_docs_content:
                counterpart_found = True
        # Also check directory-level _an counterparts
        if not counterpart_found:
            parent_name = py_file.parent.name
            if "_an" in parent_name:
                counterpart_parent = parent_name.replace("_an", "", 1)
                counterpart_dir = str(py_file).replace(
                    f"/{parent_name}/", f"/{counterpart_parent}/"
                )
                if counterpart_dir in all_docs_content:
                    counterpart_found = True
            else:
                # Try inserting _an into parent directory name
                for suffix in ("_py39", "_py310"):
                    if suffix in parent_name:
                        an_parent = parent_name.replace(suffix, f"_an{suffix}", 1)
                        break
                else:
                    an_parent = f"{parent_name}_an"
                counterpart_dir = str(py_file).replace(
                    f"/{parent_name}/", f"/{an_parent}/"
                )
                if counterpart_dir in all_docs_content:
                    counterpart_found = True
        if counterpart_found:
            continue
        logging.info(f"Removing unused file: {py_file}")
        py_file.unlink()
        removed += 1
    # Clean up directories that are empty or only contain __init__.py / __pycache__
    for dir_path in sorted(docs_src_path.rglob("*"), reverse=True):
        if not dir_path.is_dir():
            continue
        remaining = [
            f
            for f in dir_path.iterdir()
            if f.name != "__pycache__" and f.name != "__init__.py"
        ]
        if not remaining:
            logging.info(f"Removing empty/init-only directory: {dir_path}")
            shutil.rmtree(dir_path)
    print(f"Removed {removed} unused file(s) ✅")