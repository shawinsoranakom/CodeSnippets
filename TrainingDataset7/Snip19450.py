def test_template_tags_with_same_name(self):
        _engines = engines.all()
        modules = (
            "'check_framework.template_test_apps.same_tags_app_1.templatetags"
            ".same_tags', 'check_framework.template_test_apps.same_tags_app_2"
            ".templatetags.same_tags'"
        )
        errors = [self._get_error_for_engine(_engines[0], modules)]
        self.assertEqual(self._check_engines(_engines), errors)