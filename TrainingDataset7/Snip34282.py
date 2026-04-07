def test_repr(self):
        engine = Engine(
            dirs=[TEMPLATE_DIR],
            context_processors=["django.template.context_processors.debug"],
            debug=True,
            loaders=["django.template.loaders.filesystem.Loader"],
            string_if_invalid="x",
            file_charset="utf-16",
            libraries={"custom": "template_tests.templatetags.custom"},
            autoescape=False,
        )
        self.assertEqual(
            repr(engine),
            f"<Engine: dirs=[{TEMPLATE_DIR!r}] app_dirs=False "
            "context_processors=['django.template.context_processors.debug'] "
            "debug=True loaders=['django.template.loaders.filesystem.Loader'] "
            "string_if_invalid='x' file_charset='utf-16' "
            "libraries={'custom': 'template_tests.templatetags.custom'} "
            "builtins=['django.template.defaulttags', "
            "'django.template.defaultfilters', 'django.template.loader_tags'] "
            "autoescape=False>",
        )