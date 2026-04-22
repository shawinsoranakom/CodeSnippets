def test_page_sort_key(self, path_str, expected):
        assert source_util.page_sort_key(Path(path_str)) == expected