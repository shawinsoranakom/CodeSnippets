def test__logfiles(tmp_path: str):
    """ Test the _LogFiles class operates correctly

    Parameters
    ----------
    tmp_path: :class:`pathlib.Path`
    """
    # dummy logfiles + junk data
    sess_1 = os.path.join(tmp_path, "session_1", "train")
    sess_2 = os.path.join(tmp_path, "session_2", "train")
    os.makedirs(sess_1)
    os.makedirs(sess_2)

    test_log_1 = os.path.join(sess_1, "events.out.tfevents.123.456.v2")
    test_log_2 = os.path.join(sess_2, "events.out.tfevents.789.012.v2")
    test_log_junk = os.path.join(sess_2, "test_file.txt")

    for fname in (test_log_1, test_log_2, test_log_junk):
        with open(fname, "a", encoding="utf-8"):
            pass

    log_files = _LogFiles(tmp_path)
    # Test all correct
    assert isinstance(log_files._filenames, dict)
    assert len(log_files._filenames) == 2
    assert log_files._filenames == {1: test_log_1, 2: test_log_2}

    assert log_files.session_ids == [1, 2]

    assert log_files.get(1) == test_log_1
    assert log_files.get(2) == test_log_2

    # Remove a file, refresh and check again
    rmtree(sess_1)
    log_files.refresh()
    assert log_files._filenames == {2: test_log_2}
    assert log_files.get(2) == test_log_2
    assert log_files.get(3) == ""