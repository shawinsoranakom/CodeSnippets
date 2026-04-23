def test_session_initiated(self):
        session = self.client.session
        session["session_var"] = "foo"
        session.save()

        response = self.client.get("/check_session/")
        self.assertEqual(response.content, b"foo")