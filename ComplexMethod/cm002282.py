def check_auto_docstrings(overwrite: bool = False, check_all: bool = False, cache: dict[str, set[str]] | None = None):
    """
    Check docstrings of all public objects that are decorated with `@auto_docstrings`.
    This function orchestrates the process by finding relevant files, scanning for decorators,
    generating new docstrings, and updating files as needed.

    Args:
        overwrite (`bool`, *optional*, defaults to `False`):
            Whether to fix inconsistencies or not.
        check_all (`bool`, *optional*, defaults to `False`):
            Whether to check all files.
        cache (Dictionary `str` to `Set[str]`, *optional*):
            To speed up auto-docstring detection if it was previously called on a file, the cache of all previously
            computed results.
    """
    # 1. Find all model files to check
    matching_files = find_matching_model_files(check_all)
    if matching_files is None:
        return
    # 2. Find files that contain the @auto_docstring decorator
    auto_docstrings_files = find_files_with_auto_docstring(matching_files)

    # Collect all errors before raising
    has_errors = False

    # 3. For each file, update docstrings for all candidates
    for candidate_file in auto_docstrings_files:
        with open(candidate_file, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")

        # Parse file once and share the AST tree across all analysis passes
        tree = ast.parse(content)
        decorated_items = _build_ast_indexes(content, tree=tree)

        # Warm the cache so check_docstrings() won't re-parse this file
        _get_auto_docstring_names(candidate_file, cache=cache)

        missing_docstring_args_warnings = []
        fill_docstring_args_warnings = []
        docstring_args_ro_remove_warnings = []

        # Process @auto_docstring decorated items
        if decorated_items:
            missing_docstring_args_warnings, fill_docstring_args_warnings, docstring_args_ro_remove_warnings = (
                update_file_with_new_docstrings(
                    candidate_file,
                    lines,
                    decorated_items,
                    content,
                    overwrite=overwrite,
                )
            )

        # Propagate docstring fixes to the corresponding modular_*.py source so that
        # the fixes survive the next modular-converter regeneration run.  We only
        # touch a modular item when it carries an *explicit* docstring – items without
        # one inherit their docs from a parent class and must be left alone.
        _propagate_fixes_to_modular(candidate_file, decorated_items, overwrite=overwrite)

        # Process TypedDict kwargs (separate pass to avoid line number conflicts)
        # This runs AFTER @auto_docstring processing is complete
        typed_dict_missing_warnings, typed_dict_fill_warnings, typed_dict_redundant_warnings = (
            _process_typed_dict_docstrings(candidate_file, overwrite=overwrite, tree=tree)
        )

        # Report TypedDict errors
        if typed_dict_missing_warnings:
            has_errors = True
            if not overwrite:
                print(
                    "Some TypedDict fields are undocumented. Run `make fix-copies` or "
                    "`python utils/check_docstrings.py --fix_and_overwrite` to generate placeholders."
                )
            print(f"[ERROR] Undocumented fields in custom TypedDict kwargs in {candidate_file}:")
            for warning in typed_dict_missing_warnings:
                print(warning)
        if typed_dict_redundant_warnings:
            has_errors = True
            if not overwrite:
                print(
                    "Some TypedDict fields are redundant (same as source or have placeholders). "
                    "Run `make fix-copies` or `python utils/check_docstrings.py --fix_and_overwrite` to remove them."
                )
            print(f"[ERROR] Redundant TypedDict docstrings in {candidate_file}:")
            for warning in typed_dict_redundant_warnings:
                print(warning)
        if typed_dict_fill_warnings:
            has_errors = True
            print(f"[ERROR] TypedDict docstrings need to be filled in {candidate_file}:")
            for warning in typed_dict_fill_warnings:
                print(warning)
        if missing_docstring_args_warnings:
            has_errors = True
            if not overwrite:
                print(
                    "Some docstrings are missing. Run `make fix-repo` or `python utils/check_docstrings.py --fix_and_overwrite` to generate the docstring templates where needed."
                )
            print(f"[ERROR] Missing docstring for the following arguments in {candidate_file}:")
            for warning in missing_docstring_args_warnings:
                print(warning)
        if docstring_args_ro_remove_warnings:
            has_errors = True
            if not overwrite:
                print(
                    "Some docstrings are redundant with the ones in `auto_docstring.py` and will be removed. Run `make fix-repo` or `python utils/check_docstrings.py --fix_and_overwrite` to remove the redundant docstrings."
                )
            print(f"[ERROR] Redundant docstring for the following arguments in {candidate_file}:")
            for warning in docstring_args_ro_remove_warnings:
                print(warning)
        if fill_docstring_args_warnings:
            has_errors = True
            print(f"[ERROR] Docstring needs to be filled for the following arguments in {candidate_file}:")
            for warning in fill_docstring_args_warnings:
                print(warning)

    # Raise error after processing all files
    if has_errors:
        raise ValueError(
            "There was at least one problem when checking docstrings of objects decorated with @auto_docstring."
        )