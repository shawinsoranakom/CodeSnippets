def test_page_icon_and_name(self, path_str, expected):
        assert source_util.page_icon_and_name(Path(path_str)) == expected