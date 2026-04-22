def test_user_email_attr(self):
        """Test that `st.user.email` returns user info from ScriptRunContext"""
        self.assertEqual(st.experimental_user.email, "test@test.com")