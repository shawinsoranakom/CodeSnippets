def setUpClass(cls):
        cls.enterClassContext(override_settings(**TEST_SETTINGS))
        super().setUpClass()