def get_impacted_files_from_tiny_model_summary(diff_with_last_commit: bool = False) -> list[str]:
    """
    Return a list of python modeling files that are impacted by the changes of `tiny_model_summary.json` in between:

    - the current head and the main branch if `diff_with_last_commit=False` (default)
    - the current head and its parent commit otherwise.

    Returns:
        `List[str]`: The list of Python modeling files that are impacted by the changes of `tiny_model_summary.json`.
    """
    repo = Repo(PATH_TO_REPO)

    folder = Path(repo.working_dir)

    if not diff_with_last_commit:
        print(f"main is at {repo.refs.main.commit}")
        print(f"Current head is at {repo.head.commit}")

        commits = repo.merge_base(repo.refs.main, repo.head)
        for commit in commits:
            print(f"Branching commit: {commit}")
    else:
        print(f"main is at {repo.head.commit}")
        commits = repo.head.commit.parents
        for commit in commits:
            print(f"Parent commit: {commit}")

    if not os.path.isfile(folder / "tests/utils/tiny_model_summary.json"):
        return []

    files = set()
    for commit in commits:
        with checkout_commit(repo, commit):
            with open(folder / "tests/utils/tiny_model_summary.json", "r", encoding="utf-8") as f:
                old_content = f.read()

        with open(folder / "tests/utils/tiny_model_summary.json", "r", encoding="utf-8") as f:
            new_content = f.read()

        # get the content as json object
        old_content = json.loads(old_content)
        new_content = json.loads(new_content)

        old_keys = set(old_content.keys())
        new_keys = set(new_content.keys())

        # get the difference
        keys_with_diff = old_keys.symmetric_difference(new_keys)
        common_keys = old_keys.intersection(new_keys)
        # if both have the same key, check its content
        for key in common_keys:
            if old_content[key] != new_content[key]:
                keys_with_diff.add(key)

        # get the model classes
        impacted_model_classes = []
        for key in keys_with_diff:
            if key in new_keys:
                impacted_model_classes.extend(new_content[key]["model_classes"])

        # Add imports via `define_import_structure` after the #35167 as we remove explicit import in `__init__.py`
        from transformers.utils.import_utils import define_import_structure

        reversed_structure = {}
        new_imported_modules_from_import_structure = define_import_structure("src/transformers/__init__.py")
        for mapping in new_imported_modules_from_import_structure.values():
            for _module, _imports in mapping.items():
                for _import in _imports:
                    reversed_structure[_import] = _module

        # Get the corresponding modeling file path
        for model_class in impacted_model_classes:
            module = reversed_structure[model_class]
            fn = f"modeling_{module.split('.')[-1]}.py"
            files.add(f"src.transformers.{module}.{fn}".replace(".", os.path.sep).replace(f"{os.path.sep}py", ".py"))

    return sorted(files)