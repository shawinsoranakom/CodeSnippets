def setUp(self):
        self.client.force_login(self.superuser)
        self.super_login = {
            REDIRECT_FIELD_NAME: reverse("admin:index"),
            "username": "super",
            "password": "secret",
        }