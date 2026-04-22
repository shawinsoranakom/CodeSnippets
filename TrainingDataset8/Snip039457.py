def test_Credentials_activate(self):
        """Test Credentials.activate()"""
        c = Credentials.get_current()
        c.activation = None

        with patch.object(
            c, "load", side_effect=RuntimeError("Some error")
        ), patch.object(c, "save") as patched_save, patch(PROMPT) as patched_prompt:

            patched_prompt.side_effect = ["user@domain.com"]
            c.activate()
            patched_save.assert_called_once()

            self.assertEqual(c.activation.email, "user@domain.com")
            self.assertEqual(c.activation.is_valid, True)