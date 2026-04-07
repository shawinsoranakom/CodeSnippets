def test(self, call_command):
        # with a mocked call_command(), this doesn't have any effect.
        self._fixture_teardown()
        call_command.assert_called_with(
            "flush",
            interactive=False,
            allow_cascade=False,
            reset_sequences=False,
            inhibit_post_migrate=True,
            database="default",
            verbosity=0,
        )