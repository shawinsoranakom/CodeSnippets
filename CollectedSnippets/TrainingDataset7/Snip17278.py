def test_no_such_app_config(self):
        msg = "Module 'apps' does not contain a 'NoSuchConfig' class."
        with self.assertRaisesMessage(ImportError, msg):
            with self.settings(INSTALLED_APPS=["apps.NoSuchConfig"]):
                pass