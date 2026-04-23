def test_nonexistent_username(self):
        with self.assertRaisesMessage(CommandError, "user 'test' does not exist"):
            call_command("changepassword", username="test", stdout=self.stdout)