def test_beginning_with_slash_append_slash(self):
        # It can be useful to start a URL pattern with a slash when
        # APPEND_SLASH=False (#27238).
        result = check_url_config(None)
        self.assertEqual(result, [])