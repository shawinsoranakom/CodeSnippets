def test_skip_checks(self, mocked_check, *mocked_objects):
        call_command(
            "runserver",
            use_reloader=False,
            skip_checks=True,
            stdout=self.output,
        )
        self.assertNotIn("Performing system checks...", self.output.getvalue())
        mocked_check.assert_not_called()

        self.output.truncate(0)
        call_command(
            "runserver",
            use_reloader=False,
            skip_checks=False,
            stdout=self.output,
        )
        self.assertIn("Performing system checks...", self.output.getvalue())
        mocked_check.assert_has_calls(
            [mock.call(tags=set()), mock.call(display_num_errors=True)]
        )