def test_app_completion(self):
        "Application names will be autocompleted for an AppCommand"
        self._user_input("django-admin sqlmigrate a")
        output = self._run_autocomplete()
        a_labels = sorted(
            app_config.label
            for app_config in apps.get_app_configs()
            if app_config.label.startswith("a")
        )
        self.assertEqual(output, a_labels)