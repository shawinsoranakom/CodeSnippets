def setUp(self):
        super().setUp()
        localedir = os.path.join(self.test_dir, "locale")
        self.MO_FILE_HR = os.path.join(localedir, "hr/LC_MESSAGES/django.mo")
        self.MO_FILE_FR = os.path.join(localedir, "fr/LC_MESSAGES/django.mo")