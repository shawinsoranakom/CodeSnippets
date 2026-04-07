def test_that_changepassword_command_with_database_option_uses_given_db(
        self, mock_get_pass
    ):
        """
        changepassword --database should operate on the specified DB.
        """
        user = User.objects.db_manager("other").create_user(
            username="joe", password="qwerty"
        )
        self.assertTrue(user.check_password("qwerty"))

        out = StringIO()
        call_command("changepassword", username="joe", database="other", stdout=out)
        command_output = out.getvalue().strip()

        self.assertEqual(
            command_output,
            "Changing password for user 'joe'\n"
            "Password changed successfully for user 'joe'",
        )
        self.assertTrue(
            User.objects.using("other").get(username="joe").check_password("not qwerty")
        )