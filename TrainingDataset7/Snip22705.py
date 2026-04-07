def test_urlfield_clean_invalid(self):
        f = URLField()
        tests = [
            "foo",
            "com.",
            ".",
            "http://",
            "http://example",
            "http://example.",
            "http://.com",
            "http://invalid-.com",
            "http://-invalid.com",
            "http://inv-.alid-.com",
            "http://inv-.-alid.com",
            "[a",
            "http://[a",
            # Non-string.
            23,
            # Hangs "forever" before fixing a catastrophic backtracking,
            # see #11198.
            "http://%s" % ("X" * 60,),
            # A second example, to make sure the problem is really addressed,
            # even on domains that don't fail the domain label length check in
            # the regex.
            "http://%s" % ("X" * 200,),
            # Scheme prepend yields a structurally invalid URL.
            "////]@N.AN",
            # Scheme prepend yields an empty hostname.
            "#@A.bO",
            # Known problematic unicode chars.
            "http://" + "¾" * 200,
            # Non-ASCII character before the first colon.
            "¾:example.com",
            # ASCII digit before the first colon.
            "1http://example.com",
            # Empty scheme.
            "://example.com",
            ":example.com",
        ]
        msg = "'Enter a valid URL.'"
        for value in tests:
            with self.subTest(value=value):
                with self.assertRaisesMessage(ValidationError, msg):
                    f.clean(value)