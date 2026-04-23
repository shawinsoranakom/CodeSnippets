def get_all_tests() -> list[str]:
    """
    Walks the `tests` folder to return a list of files/subfolders. This is used to split the tests to run when using
    parallelism. The split is:

    - folders under `tests`: (`tokenization`, `pipelines`, etc) except the subfolder `models` is excluded.
    - folders under `tests/models`: `bert`, `gpt2`, etc.
    - test files under `tests`: `test_modeling_common.py`, `test_tokenization_common.py`, etc.
    """

    # test folders/files directly under `tests` folder
    tests = os.listdir(PATH_TO_TESTS)
    tests = [f"tests/{f}" for f in tests if "__pycache__" not in f]
    tests = sorted([f for f in tests if (PATH_TO_REPO / f).is_dir() or f.startswith("tests/test_")])

    # model specific test folders
    model_test_folders = os.listdir(PATH_TO_TESTS / "models")
    model_test_folders = [f"tests/models/{f}" for f in model_test_folders if "__pycache__" not in f]
    model_test_folders = sorted([f for f in model_test_folders if (PATH_TO_REPO / f).is_dir()])

    tests.remove("tests/models")
    # Sagemaker tests are not meant to be run on the CI.
    if "tests/sagemaker" in tests:
        tests.remove("tests/sagemaker")
    tests = model_test_folders + tests

    return tests