def test_template_tags_with_different_library_name(self):
        with self.settings(
            TEMPLATES=[
                self.get_settings(
                    "same_tags",
                    "same_tags_app_1.templatetags.same_tags",
                    name="backend_1",
                ),
                self.get_settings(
                    "not_same_tags",
                    "same_tags_app_2.templatetags.same_tags",
                    name="backend_2",
                ),
            ]
        ):
            self.assertEqual(self._check_engines(engines.all()), [])