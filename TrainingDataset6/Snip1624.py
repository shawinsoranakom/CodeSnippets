def test_how_to_configure(self, shell):
        assert not shell.how_to_configure().can_configure_automatically