def test_sessionmanager_save(self):
        """
        Test SessionManager.save method
        """
        # Create a session
        self.session["y"] = 1
        self.session.save()

        s = self.model.objects.get(session_key=self.session.session_key)
        # Change it
        self.model.objects.save(s.session_key, {"y": 2}, s.expire_date)
        # Clear cache, so that it will be retrieved from DB
        del self.session._session_cache
        self.assertEqual(self.session["y"], 2)