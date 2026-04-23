def test_session_modifying_view(self):
        "Request a page that modifies the session"
        # Session value isn't set initially
        with self.assertRaises(KeyError):
            self.client.session["tobacconist"]

        self.client.post("/session_view/")
        # The session was modified
        self.assertEqual(self.client.session["tobacconist"], "hovercraft")