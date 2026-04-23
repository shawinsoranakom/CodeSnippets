def test_translated_regex_compiled_per_language(self):
        provider = RegexPattern(translation.gettext_lazy("^foo/$"))
        with translation.override("de"):
            de_compiled = provider.regex
            # compiled only once per language
            error = AssertionError(
                "tried to compile url regex twice for the same language"
            )
            with mock.patch("django.urls.resolvers.re.compile", side_effect=error):
                de_compiled_2 = provider.regex
        with translation.override("fr"):
            fr_compiled = provider.regex
        self.assertEqual(fr_compiled.pattern, "^foo-fr/$")
        self.assertEqual(de_compiled.pattern, "^foo-de/$")
        self.assertEqual(de_compiled, de_compiled_2)