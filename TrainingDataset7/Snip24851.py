def test_invalid_cookies(self):
        """
        Cookie strings that go against RFC 6265 but browsers will send if set
        via document.cookie.
        """
        # Chunks without an equals sign appear as unnamed values per
        # https://bugzilla.mozilla.org/show_bug.cgi?id=169091
        self.assertIn(
            "django_language", parse_cookie("abc=def; unnamed; django_language=en")
        )
        # Even a double quote may be an unnamed value.
        self.assertEqual(parse_cookie('a=b; "; c=d'), {"a": "b", "": '"', "c": "d"})
        # Spaces in names and values, and an equals sign in values.
        self.assertEqual(
            parse_cookie("a b c=d e = f; gh=i"), {"a b c": "d e = f", "gh": "i"}
        )
        # More characters the spec forbids.
        self.assertEqual(
            parse_cookie('a   b,c<>@:/[]?{}=d  "  =e,f g'),
            {"a   b,c<>@:/[]?{}": 'd  "  =e,f g'},
        )
        # Unicode characters. The spec only allows ASCII.
        self.assertEqual(
            parse_cookie("saint=André Bessette"), {"saint": "André Bessette"}
        )
        # Browsers don't send extra whitespace or semicolons in Cookie headers,
        # but parse_cookie() should parse whitespace the same way
        # document.cookie parses whitespace.
        self.assertEqual(
            parse_cookie("  =  b  ;  ;  =  ;   c  =  ;  "), {"": "b", "c": ""}
        )