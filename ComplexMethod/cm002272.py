def find_matching_model_files(check_all: bool = False):
    """
    Find all model files in the transformers repo that should be checked for @auto_docstring,
    excluding files with certain substrings.
    Returns:
        List of file paths.
    """
    module_diff_files = None
    if not check_all:
        module_diff_files = set()
        repo = Repo(PATH_TO_REPO)
        # Diff from index to unstaged files
        for modified_file_diff in repo.index.diff(None):
            if modified_file_diff.a_path.startswith("src/transformers"):
                module_diff_files.add(os.path.join(PATH_TO_REPO, modified_file_diff.a_path))
        # Diff from index to `main`
        for modified_file_diff in repo.index.diff(repo.refs.main.commit):
            if modified_file_diff.a_path.startswith("src/transformers"):
                module_diff_files.add(os.path.join(PATH_TO_REPO, modified_file_diff.a_path))
        # quick escape route: if there are no module files in the diff, skip this check
        if len(module_diff_files) == 0:
            return None

    modeling_glob_pattern = os.path.join(PATH_TO_TRANSFORMERS, "models/**/modeling_**")
    potential_files = glob.glob(modeling_glob_pattern)
    image_processing_glob_pattern = os.path.join(PATH_TO_TRANSFORMERS, "models/**/image_processing_*_fast.py")
    potential_files += glob.glob(image_processing_glob_pattern)
    processing_glob_pattern = os.path.join(PATH_TO_TRANSFORMERS, "models/**/processing_*.py")
    potential_files += glob.glob(processing_glob_pattern)
    configuration_glob_pattern = os.path.join(PATH_TO_TRANSFORMERS, "models/**/configuration_*.py")
    potential_files += glob.glob(configuration_glob_pattern)
    matching_files = []
    for file_path in potential_files:
        if os.path.isfile(file_path):
            matching_files.append(file_path)
    if not check_all:
        # intersect with module_diff_files
        matching_files = sorted([file for file in matching_files if file in module_diff_files])

    return matching_files