def test_multiple_default(self):
        class MultipleFileInput(FileInput):
            allow_multiple_selected = True

        tests = [
            (None, True),
            ({"class": "myclass"}, True),
            ({"multiple": False}, False),
        ]
        for attrs, expected in tests:
            with self.subTest(attrs=attrs):
                widget = MultipleFileInput(attrs=attrs)
                self.assertIs(widget.attrs["multiple"], expected)