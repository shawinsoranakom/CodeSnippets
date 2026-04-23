def test_skip_if_not_in_TTY(self):
        """
        If the command is not called from a TTY, it should be skipped and a
        message should be displayed (#7423).
        """

        class FakeStdin:
            """A fake stdin object that has isatty() return False."""

            def isatty(self):
                return False

        out = StringIO()
        call_command(
            "createsuperuser",
            stdin=FakeStdin(),
            stdout=out,
            interactive=True,
        )

        self.assertEqual(User._default_manager.count(), 0)
        self.assertIn("Superuser creation skipped", out.getvalue())