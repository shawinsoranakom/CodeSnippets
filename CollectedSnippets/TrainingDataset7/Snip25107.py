def test_admin_javascript_supported_input_formats(self):
        """
        The first input format for DATE_INPUT_FORMATS, TIME_INPUT_FORMATS, and
        DATETIME_INPUT_FORMATS must not contain %f since that's unsupported by
        the admin's time picker widget.
        """
        regex = re.compile("%([^BcdHImMpSwxXyY%])")
        for language_code, language_name in settings.LANGUAGES:
            for format_name in (
                "DATE_INPUT_FORMATS",
                "TIME_INPUT_FORMATS",
                "DATETIME_INPUT_FORMATS",
            ):
                with self.subTest(language=language_code, format=format_name):
                    formatter = get_format(format_name, lang=language_code)[0]
                    self.assertEqual(
                        regex.findall(formatter),
                        [],
                        "%s locale's %s uses an unsupported format code."
                        % (language_code, format_name),
                    )