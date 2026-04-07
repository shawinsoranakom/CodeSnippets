def test_init(self):
        "Testing GeometryField initialization with defaults."
        fld = forms.GeometryField()
        for bad_default in ("blah", 3, "FoO", None, 0):
            with self.subTest(bad_default=bad_default):
                with self.assertRaises(ValidationError):
                    fld.clean(bad_default)