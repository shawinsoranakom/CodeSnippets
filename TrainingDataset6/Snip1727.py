def test_when_cant_match(self):
        assert 'status' == get_closest('st', ['status', 'reset'])