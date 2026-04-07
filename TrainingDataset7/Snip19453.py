def test_template_tags_with_same_library_name_and_module_name(self):
        modules = (
            "'check_framework.template_test_apps.different_tags_app.templatetags"
            ".different_tags', 'check_framework.template_test_apps.same_tags_app_1"
            ".templatetags.same_tags'"
        )
        with self.settings(
            TEMPLATES=[
                self.get_settings(
                    "same_tags", "different_tags_app.templatetags.different_tags"
                ),
            ]
        ):
            _engines = engines.all()
            errors = [self._get_error_for_engine(_engines[0], modules)]
            self.assertEqual(self._check_engines(_engines), errors)