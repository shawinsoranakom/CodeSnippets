def test_when_can_match(self):
        assert 'branch' == get_closest('brnch', ['branch', 'status'])