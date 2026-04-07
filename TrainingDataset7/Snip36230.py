def test_invalid_time_format_specifiers(self):
        my_birthday = date(1984, 8, 7)

        for specifier in ["a", "A", "f", "g", "G", "h", "H", "i", "P", "s", "u"]:
            with self.subTest(specifier=specifier):
                msg = (
                    "The format for date objects may not contain time-related "
                    f"format specifiers (found {specifier!r})."
                )
                with self.assertRaisesMessage(TypeError, msg):
                    dateformat.format(my_birthday, specifier)