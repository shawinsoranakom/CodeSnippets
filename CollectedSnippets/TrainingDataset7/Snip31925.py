def test_session_str(self):
        "Session repr should be the session key."
        self.session["x"] = 1
        self.session.save()

        session_key = self.session.session_key
        s = self.model.objects.get(session_key=session_key)

        self.assertEqual(str(s), session_key)