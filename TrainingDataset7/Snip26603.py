def test_disallowed_user_agents(self):
        request = self.rf.get("/slash")
        request.META["HTTP_USER_AGENT"] = "foo"
        with self.assertRaisesMessage(PermissionDenied, "Forbidden user agent"):
            CommonMiddleware(get_response_empty).process_request(request)