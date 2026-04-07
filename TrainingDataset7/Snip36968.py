def test_setting_allows_custom_subclass(self):
        self.assertIsInstance(
            get_default_exception_reporter_filter(),
            CustomExceptionReporterFilter,
        )