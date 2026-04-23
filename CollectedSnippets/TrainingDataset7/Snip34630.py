def test_force_login_without_backend(self):
        """
        force_login() without passing a backend and with multiple backends
        configured should automatically use the first backend.
        """
        self.client.force_login(self.u1)
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")
        self.assertEqual(self.u1.backend, "django.contrib.auth.backends.ModelBackend")