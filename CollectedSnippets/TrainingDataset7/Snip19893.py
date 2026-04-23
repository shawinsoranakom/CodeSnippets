def test_model_name_max_length(self):
        type("A" * 100, (models.Model,), {"__module__": self.__module__})
        self.assertEqual(check_model_name_lengths(self.apps.get_app_configs()), [])