def check_docstrings(overwrite: bool = False, check_all: bool = False, cache: dict[str, set[str]] | None = None):
    """
    Check docstrings of all public objects that are callables and are documented. By default, only checks the diff.

    Args:
        overwrite (`bool`, *optional*, defaults to `False`):
            Whether to fix inconsistencies or not.
        check_all (`bool`, *optional*, defaults to `False`):
            Whether to check all files.
        cache (Dictionary `str` to `Set[str]`, *optional*):
            To speed up auto-docstring detection if it was previously called on a file, the cache of all previously
            computed results.
    """
    module_diff_files = None
    if not check_all:
        module_diff_files = set()
        repo = Repo(PATH_TO_REPO)
        # Diff from index to unstaged files
        for modified_file_diff in repo.index.diff(None):
            if modified_file_diff.a_path.startswith("src/transformers"):
                module_diff_files.add(modified_file_diff.a_path)
        # Diff from index to `main`
        for modified_file_diff in repo.index.diff(repo.refs.main.commit):
            if modified_file_diff.a_path.startswith("src/transformers"):
                module_diff_files.add(modified_file_diff.a_path)
        # quick escape route: if there are no module files in the diff, skip this check
        if len(module_diff_files) == 0:
            return

    failures = []
    hard_failures = []
    to_clean = []
    for name in dir(transformers):
        # Skip objects that are private or not documented.
        if (
            any(name.startswith(prefix) for prefix in OBJECT_TO_IGNORE_PREFIXES)
            or ignore_undocumented(name)
            or name in OBJECTS_TO_IGNORE
        ):
            continue

        obj = getattr(transformers, name)
        if not callable(obj) or not isinstance(obj, type) or getattr(obj, "__doc__", None) is None:
            continue

        # If we are checking against the diff, we skip objects that are not part of the diff.
        if module_diff_files is not None:
            object_file = find_source_file(getattr(transformers, name))
            object_file_relative_path = "src/" + str(object_file).split("/src/")[1]
            if object_file_relative_path not in module_diff_files:
                continue

        # Skip objects decorated with @auto_docstring - they have auto-generated documentation
        if has_auto_docstring_decorator(obj, cache=cache):
            continue

        # Check docstring
        try:
            result = match_docstring_with_signature(obj)
            if result is not None:
                old_doc, new_doc = result
            else:
                old_doc, new_doc = None, None
        except Exception as e:
            print(e)
            hard_failures.append(name)
            continue
        if old_doc != new_doc:
            if overwrite:
                fix_docstring(obj, old_doc, new_doc)
            else:
                failures.append(name)
        elif not overwrite and new_doc is not None and ("<fill_type>" in new_doc or "<fill_docstring>" in new_doc):
            to_clean.append(name)

    # Deal with errors
    error_message = ""
    if len(hard_failures) > 0:
        error_message += (
            "The argument part of the docstrings of the following objects could not be processed, check they are "
            "properly formatted."
        )
        error_message += "\n" + "\n".join([f"- {name}" for name in hard_failures])
    if len(failures) > 0:
        error_message += (
            "The following objects docstrings do not match their signature. Run `make fix-repo` to fix this. "
            "In some cases, this error may be raised incorrectly by the docstring checker. If you think this is the "
            "case, you can manually check the docstrings and then add the object name to `OBJECTS_TO_IGNORE` in "
            "`utils/check_docstrings.py`."
        )
        error_message += "\n" + "\n".join([f"- {name}" for name in failures])
    if len(to_clean) > 0:
        error_message += (
            "The following objects docstrings contain templates you need to fix: search for `<fill_type>` or "
            "`<fill_docstring>`."
        )
        error_message += "\n" + "\n".join([f"- {name}" for name in to_clean])

    if len(error_message) > 0:
        error_message = "There was at least one problem when checking docstrings of public objects.\n" + error_message
        raise ValueError(error_message)