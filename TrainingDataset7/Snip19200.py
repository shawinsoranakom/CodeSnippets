def test_has_key_race_handling(self):
        self.assertIs(cache.add("key", "value"), True)
        with mock.patch("builtins.open", side_effect=FileNotFoundError) as mocked_open:
            self.assertIs(cache.has_key("key"), False)
            mocked_open.assert_called_once()