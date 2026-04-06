def test_get_all_executables_exclude_paths(path, pathsep, excluded, settings):
    settings.init()
    settings.excluded_search_path_prefixes = [excluded]
    with patch('thefuck.utils.Path') as Path_mock:
        get_all_executables()
        path_list = path.split(pathsep)
        assert call(path_list[-1]) not in Path_mock.mock_calls
        assert all(call(p) in Path_mock.mock_calls for p in path_list[:-1])