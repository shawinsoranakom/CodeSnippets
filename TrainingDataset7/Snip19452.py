def test_template_tags_same_library_in_installed_apps_libraries(self):
        with self.settings(
            TEMPLATES=[
                self.get_settings(
                    "same_tags", "same_tags_app_1.templatetags.same_tags"
                ),
            ]
        ):
            self.assertEqual(self._check_engines(engines.all()), [])