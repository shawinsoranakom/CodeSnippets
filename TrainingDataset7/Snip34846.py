def test_should_set_correct_env_variables(self):
        request = RequestFactory().get("/path/")

        self.assertEqual(request.META.get("REMOTE_ADDR"), "127.0.0.1")
        self.assertEqual(request.META.get("SERVER_NAME"), "testserver")
        self.assertEqual(request.META.get("SERVER_PORT"), "80")
        self.assertEqual(request.META.get("SERVER_PROTOCOL"), "HTTP/1.1")
        self.assertEqual(
            request.META.get("SCRIPT_NAME") + request.META.get("PATH_INFO"), "/path/"
        )