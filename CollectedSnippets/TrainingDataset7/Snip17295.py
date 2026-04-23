def test_models_py(self):
        """
        The models in the models.py file were loaded correctly.
        """
        self.assertEqual(apps.get_model("apps", "TotallyNormal"), TotallyNormal)
        with self.assertRaises(LookupError):
            apps.get_model("apps", "SoAlternative")

        with self.assertRaises(LookupError):
            new_apps.get_model("apps", "TotallyNormal")
        self.assertEqual(new_apps.get_model("apps", "SoAlternative"), SoAlternative)