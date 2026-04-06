def test_isnt_match(self):
        assert not Rule('', lambda _: False).is_match(
            Command('ls', ''))