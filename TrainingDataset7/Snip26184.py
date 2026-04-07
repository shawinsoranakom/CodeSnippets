def setUpClass(cls):
        cls.enterClassContext(override_settings(EMAIL_BACKEND=cls.email_backend))
        super().setUpClass()