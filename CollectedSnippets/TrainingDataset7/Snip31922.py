def test_session_save_does_not_resurrect_session_logged_out_in_other_context(self):
        """
        Sessions shouldn't be resurrected by a concurrent request.
        """
        # Create new session.
        s1 = self.backend()
        s1["test_data"] = "value1"
        s1.save(must_create=True)

        # Logout in another context.
        s2 = self.backend(s1.session_key)
        s2.delete()

        # Modify session in first context.
        s1["test_data"] = "value2"
        with self.assertRaises(UpdateError):
            # This should throw an exception as the session is deleted, not
            # resurrect the session.
            s1.save()

        self.assertEqual(s1.load(), {})