def test_clearsessions_command(self):
        """
        Test clearsessions command for clearing expired sessions.
        """
        storage_path = self.backend._get_storage_path()
        file_prefix = settings.SESSION_COOKIE_NAME

        def count_sessions():
            return len(
                [
                    session_file
                    for session_file in os.listdir(storage_path)
                    if session_file.startswith(file_prefix)
                ]
            )

        self.assertEqual(0, count_sessions())

        # One object in the future
        self.session["foo"] = "bar"
        self.session.set_expiry(3600)
        self.session.save()

        # One object in the past
        other_session = self.backend()
        other_session["foo"] = "bar"
        other_session.set_expiry(-3600)
        other_session.save()

        # One object in the present without an expiry (should be deleted since
        # its modification time + SESSION_COOKIE_AGE will be in the past when
        # clearsessions runs).
        other_session2 = self.backend()
        other_session2["foo"] = "bar"
        other_session2.save()

        # Three sessions are in the filesystem before clearsessions...
        self.assertEqual(3, count_sessions())
        management.call_command("clearsessions")
        # ... and two are deleted.
        self.assertEqual(1, count_sessions())