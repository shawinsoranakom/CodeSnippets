def test_session_get_decoded(self):
        """
        Test we can use Session.get_decoded to retrieve data stored
        in normal way
        """
        self.session["x"] = 1
        self.session.save()

        s = self.model.objects.get(session_key=self.session.session_key)

        self.assertEqual(s.get_decoded(), {"x": 1})