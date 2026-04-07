def test_nontranslated_regex_compiled_once(self):
        provider = RegexPattern("^foo/$")
        with translation.override("de"):
            de_compiled = provider.regex
        with translation.override("fr"):
            # compiled only once, regardless of language
            error = AssertionError("tried to compile non-translated url regex twice")
            with mock.patch("django.urls.resolvers.re.compile", side_effect=error):
                fr_compiled = provider.regex
        self.assertEqual(de_compiled.pattern, "^foo/$")
        self.assertEqual(fr_compiled.pattern, "^foo/$")