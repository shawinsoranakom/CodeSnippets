def test_other_create_with_suggested_username(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                verbosity=0,
                database="other",
            )
            self.assertIs(qs.filter(username=default_username).exists(), True)