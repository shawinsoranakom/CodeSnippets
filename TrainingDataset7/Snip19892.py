def test_model_name_too_long(self):
        model = type("A" * 101, (models.Model,), {"__module__": self.__module__})
        self.assertEqual(
            check_model_name_lengths(self.apps.get_app_configs()),
            [
                checks.Error(
                    "Model names must be at most 100 characters (got 101).",
                    obj=model,
                    id="contenttypes.E005",
                )
            ],
        )