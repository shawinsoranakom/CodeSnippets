def test_get_serialized_nonexistent_id(self):
        assert self.wstates.get_serialized("nonexistent_id") is None