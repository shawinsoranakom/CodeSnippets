def test_page_sort_key_error(self):
        with pytest.raises(AssertionError) as e:
            source_util.page_sort_key(Path("/foo/bar/baz.rs"))

        assert str(e.value) == "/foo/bar/baz.rs is not a Python file"