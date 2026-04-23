def test_passing_stdin(self):
        """
        You can pass a stdin object as an option and it should be
        available on self.stdin.
        If no such option is passed, it defaults to sys.stdin.
        """
        sentinel = object()
        command = createsuperuser.Command()
        call_command(
            command,
            stdin=sentinel,
            interactive=False,
            verbosity=0,
            username="janet",
            email="janet@example.com",
        )
        self.assertIs(command.stdin, sentinel)

        command = createsuperuser.Command()
        call_command(
            command,
            interactive=False,
            verbosity=0,
            username="joe",
            email="joe@example.com",
        )
        self.assertIs(command.stdin, sys.stdin)