def test_tuple_settings(self):
        settings_module = ModuleType("fake_settings_module")
        settings_module.SECRET_KEY = "foo"
        msg = "The %s setting must be a list or a tuple."
        for setting in self.list_or_tuple_settings:
            setattr(settings_module, setting, ("non_list_or_tuple_value"))
            sys.modules["fake_settings_module"] = settings_module
            try:
                with self.assertRaisesMessage(ImproperlyConfigured, msg % setting):
                    Settings("fake_settings_module")
            finally:
                del sys.modules["fake_settings_module"]
                delattr(settings_module, setting)