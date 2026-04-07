def test_repr_empty(self):
        engine = Engine()
        self.assertEqual(
            repr(engine),
            "<Engine: app_dirs=False debug=False loaders=[("
            "'django.template.loaders.cached.Loader', "
            "['django.template.loaders.filesystem.Loader'])] "
            "string_if_invalid='' file_charset='utf-8' builtins=["
            "'django.template.defaulttags', 'django.template.defaultfilters', "
            "'django.template.loader_tags'] autoescape=True>",
        )