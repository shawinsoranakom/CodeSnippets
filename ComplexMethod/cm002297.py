def get_all_doctest_files() -> list[str]:
    """
    Return the complete list of python and Markdown files on which we run doctest.

    At this moment, we restrict this to only take files from `src/` or `docs/source/en/` that are not in `utils/not_doctested.txt`.

    Returns:
        `List[str]`: The complete list of Python and Markdown files on which we run doctest.
    """
    py_files = [str(x.relative_to(PATH_TO_REPO)) for x in PATH_TO_REPO.glob("**/*.py")]
    md_files = [str(x.relative_to(PATH_TO_REPO)) for x in PATH_TO_REPO.glob("**/*.md")]

    test_files_to_run = py_files + md_files
    # change to use "/" as path separator
    test_files_to_run = ["/".join(Path(x).parts) for x in test_files_to_run]
    # don't run doctest for files in `src/transformers/models/deprecated`
    test_files_to_run = [x for x in test_files_to_run if "models/deprecated" not in x]

    # only include files in `src` or `docs/source/en/`
    test_files_to_run = [x for x in test_files_to_run if x.startswith(("src/", "docs/source/en/"))]
    # not include init files
    test_files_to_run = [x for x in test_files_to_run if not x.endswith(("__init__.py",))]

    # These are files not doctested yet.
    with open("utils/not_doctested.txt") as fp:
        not_doctested = {x.split(" ")[0] for x in fp.read().strip().split("\n")}

    # So far we don't have 100% coverage for doctest. This line will be removed once we achieve 100%.
    test_files_to_run = [x for x in test_files_to_run if x not in not_doctested]

    return sorted(test_files_to_run)