def test_bad_handlers_invalid_path(self):
        result = check_custom_error_handlers(None)
        paths = [
            "django.views.bad_handler",
            "django.invalid_module.bad_handler",
            "invalid_module.bad_handler",
            "django",
        ]
        hints = [
            "Could not import '{}'. View does not exist in module django.views.",
            "Could not import '{}'. Parent module django.invalid_module does not "
            "exist.",
            "No module named 'invalid_module'",
            "Could not import '{}'. The path must be fully qualified.",
        ]
        for code, path, hint, error in zip([400, 403, 404, 500], paths, hints, result):
            with self.subTest("handler{}".format(code)):
                self.assertEqual(
                    error,
                    Error(
                        "The custom handler{} view '{}' could not be imported.".format(
                            code, path
                        ),
                        hint=hint.format(path),
                        id="urls.E008",
                    ),
                )