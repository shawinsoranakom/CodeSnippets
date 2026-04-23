def pytest_runtest_setup(item):
    fname = item.fspath.strpath
    # normalize filename to use forward slashes on Windows for easier handling
    # later
    fname = fname.replace(os.sep, "/")

    is_index = fname.endswith("datasets/index.rst")
    if fname.endswith("datasets/labeled_faces.rst") or is_index:
        setup_labeled_faces()
    elif fname.endswith("datasets/rcv1.rst") or is_index:
        setup_rcv1()
    elif fname.endswith("datasets/twenty_newsgroups.rst") or is_index:
        setup_twenty_newsgroups()
    elif fname.endswith("modules/compose.rst") or is_index:
        setup_compose()
    elif fname.endswith("datasets/loading_other_datasets.rst"):
        setup_loading_other_datasets()
    elif fname.endswith("modules/impute.rst"):
        setup_impute()
    elif fname.endswith("modules/grid_search.rst"):
        setup_grid_search()
    elif fname.endswith("modules/preprocessing.rst"):
        setup_preprocessing()

    rst_files_requiring_matplotlib = [
        "modules/partial_dependence.rst",
        "modules/tree.rst",
    ]
    for each in rst_files_requiring_matplotlib:
        if fname.endswith(each):
            skip_if_matplotlib_not_installed(fname)

    if fname.endswith("array_api.rst"):
        skip_if_cupy_not_installed(fname)