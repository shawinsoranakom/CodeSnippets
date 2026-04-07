def test_template_tags_for_separate_backends(self):
        # The "libraries" names are the same, but the backends are different.
        with self.settings(
            TEMPLATES=[
                self.get_settings(
                    "same_tags",
                    "same_tags_app_1.templatetags.same_tags",
                    name="backend_1",
                ),
                self.get_settings(
                    "same_tags",
                    "same_tags_app_2.templatetags.same_tags",
                    name="backend_2",
                ),
            ]
        ):
            self.assertEqual(self._check_engines(engines.all()), [])