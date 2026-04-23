def test_get_folder(tmp_path: str) -> None:
    """ Unit test for :func:`~lib.utils.get_folder`

    Parameters
    ----------
    tmp_path: str
        pytest temporary path to generate folders
    """
    # New folder
    path = os.path.join(tmp_path, "test_new_folder")
    expected_output = path
    assert not os.path.isdir(path)
    assert get_folder(path) == expected_output
    assert os.path.isdir(path)

    # Test not creating a new folder when it already exists
    path = os.path.join(tmp_path, "test_new_folder")
    expected_output = path
    assert os.path.isdir(path)
    stats = os.stat(path)
    assert get_folder(path) == expected_output
    assert os.path.isdir(path)
    assert stats == os.stat(path)

    # Test not creating a new folder when make_folder is False
    path = os.path.join(tmp_path, "test_no_folder")
    expected_output = ""
    assert get_folder(path, make_folder=False) == expected_output
    assert not os.path.isdir(path)