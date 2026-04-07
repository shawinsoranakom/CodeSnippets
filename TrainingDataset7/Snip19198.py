def test_get_does_not_ignore_non_filenotfound_exceptions(self):
        with mock.patch("builtins.open", side_effect=OSError):
            with self.assertRaises(OSError):
                cache.get("foo")