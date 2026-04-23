def create_test_files(
    repo_path: Path, old_model_infos: ModelInfos, new_lowercase_name, filenames_to_add: list[tuple[str, bool]]
):
    """
    Create the test files for the new model. It basically copies over the old test files and adjust the class names.

    Args:
        old_model_infos (`ModelInfos`):
            The structure containing the class information of the old model.
        new_lowercase_name (`str`):
            The new lowercase model name.
        filenames_to_add (`list[tuple[str, bool]]`):
            A list of tuples of all potential filenames to add for a new model, along a boolean flag describing if we
            should add this file or not. For example, [(`modeling_xxx.px`, True), (`configuration_xxx.py`, True), (`tokenization_xxx.py`, False),...]
    """
    new_cased_name = "".join(x.title() for x in new_lowercase_name.replace("-", "_").split("_"))
    old_lowercase_name = old_model_infos.lowercase_name
    old_cased_name = old_model_infos.camelcase_name
    filenames_to_add = [
        ("test_" + filename.replace(old_lowercase_name, new_lowercase_name), to_add)
        for filename, to_add in filenames_to_add[1:]
    ]
    # fast tokenizer/image processor have the same test files as normal ones
    corrected_filenames_to_add = []
    for file, to_add in filenames_to_add:
        if re.search(rf"test_(?:tokenization)|(?:image_processing)_{new_lowercase_name}_fast.py", file):
            previous_file, previous_to_add = corrected_filenames_to_add[-1]
            corrected_filenames_to_add[-1] = (previous_file, previous_to_add or to_add)
        else:
            corrected_filenames_to_add.append((file, to_add))

    test_files = {}
    for new_file, to_add in corrected_filenames_to_add:
        if to_add:
            original_test_file = new_file.replace(new_lowercase_name, old_lowercase_name)
            original_test_path = repo_path / "tests" / "models" / old_lowercase_name / original_test_file
            # Sometimes, tests may not exist
            if not original_test_path.is_file():
                continue
            with open(original_test_path, "r") as f:
                test_code = f.read()
            # Remove old copyright and add new one
            test_lines = test_code.split("\n")
            idx = 0
            while test_lines[idx].startswith("#"):
                idx += 1
            test_code = COPYRIGHT + "\n".join(test_lines[idx:])
            test_files[new_file] = test_code.replace(old_cased_name, new_cased_name)

    return test_files