def test_other_no_suggestion(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                verbosity=0,
                database="other",
            )
            self.assertIs(qs.filter(username="other").exists(), True)