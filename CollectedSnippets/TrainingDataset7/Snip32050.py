def test_module(self):
        settings_module = ModuleType("fake_settings_module")
        settings_module.SECRET_KEY = "foo"
        settings_module.USE_TZ = False
        sys.modules["fake_settings_module"] = settings_module
        try:
            s = Settings("fake_settings_module")

            self.assertTrue(s.is_overridden("SECRET_KEY"))
            self.assertFalse(s.is_overridden("ALLOWED_HOSTS"))
        finally:
            del sys.modules["fake_settings_module"]