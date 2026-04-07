def test_locale_not_interepreted_as_regex(self):
        with translation.override("e("):
            # Would previously error:
            # re.error: missing ), unterminated subpattern at position 1
            reverse("users")