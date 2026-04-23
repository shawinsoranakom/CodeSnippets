def test_session_not_accessed(self):
        """
        The session is not accessed simply by including
        the auth context processor
        """
        response = self.client.get("/auth_processor_no_attr_access/")
        self.assertContains(response, "Session not accessed")