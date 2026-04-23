def test_createsuperuser_command_suggested_username_with_database_option(self):
        default_username = get_default_username(database="other")
        qs = User.objects.using("other")

        @mock_inputs({"password": "nopasswd", "username": "", "email": ""})
        def test_other_create_with_suggested_username(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                verbosity=0,
                database="other",
            )
            self.assertIs(qs.filter(username=default_username).exists(), True)

        test_other_create_with_suggested_username(self)

        @mock_inputs({"password": "nopasswd", "Username: ": "other", "email": ""})
        def test_other_no_suggestion(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                verbosity=0,
                database="other",
            )
            self.assertIs(qs.filter(username="other").exists(), True)

        test_other_no_suggestion(self)