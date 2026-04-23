def test_run_from_argv_closes_connections(self):
        """
        A command called from the command line should close connections after
        being executed (#21255).
        """
        command = BaseCommand()
        command.check = lambda: []
        command.handle = lambda *args, **kwargs: args
        with mock.patch("django.core.management.base.connections") as mock_connections:
            command.run_from_argv(["", ""])
        # Test connections have been closed
        self.assertTrue(mock_connections.close_all.called)