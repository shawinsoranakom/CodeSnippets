def test_no_such_app_config_with_choices(self):
        msg = (
            "Module 'apps.apps' does not contain a 'NoSuchConfig' class. "
            "Choices are: 'BadConfig', 'ModelPKAppsConfig', 'MyAdmin', "
            "'MyAuth', 'NoSuchApp', 'PlainAppsConfig', 'RelabeledAppsConfig'."
        )
        with self.assertRaisesMessage(ImportError, msg):
            with self.settings(INSTALLED_APPS=["apps.apps.NoSuchConfig"]):
                pass