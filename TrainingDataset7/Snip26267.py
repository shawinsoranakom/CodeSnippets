def setUpClass(cls):
        super().setUpClass()
        cls.backend = smtp.EmailBackend(username="", password="")
        cls.smtp_controller.stop()