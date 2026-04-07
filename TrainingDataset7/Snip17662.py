def test_session_is_accessed(self):
        """
        The session is accessed if the auth context processor
        is used and relevant attributes accessed.
        """
        response = self.client.get("/auth_processor_attr_access/")
        self.assertContains(response, "Session accessed")