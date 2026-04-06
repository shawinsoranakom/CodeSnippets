def test_get_all_executables_pathsep(path, pathsep):
    with patch('thefuck.utils.Path') as Path_mock:
        get_all_executables()
        Path_mock.assert_has_calls([call(p) for p in path.split(pathsep)], True)