def setUp(self):
        super().setUp()
        self.write_settings(
            "settings.py",
            extra=(
                "from django.urls import reverse_lazy\n"
                "LOGIN_URL = reverse_lazy('login')"
            ),
        )