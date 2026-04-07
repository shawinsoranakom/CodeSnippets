def test_date_formats(self):
        # Specifiers 'I', 'r', and 'U' are covered in test_timezones().
        my_birthday = datetime(1979, 7, 8, 22, 00)
        for specifier, expected in [
            ("b", "jul"),
            ("d", "08"),
            ("D", "Sun"),
            ("E", "July"),
            ("F", "July"),
            ("j", "8"),
            ("l", "Sunday"),
            ("L", "False"),
            ("m", "07"),
            ("M", "Jul"),
            ("n", "7"),
            ("N", "July"),
            ("o", "1979"),
            ("S", "th"),
            ("t", "31"),
            ("w", "0"),
            ("W", "27"),
            ("y", "79"),
            ("Y", "1979"),
            ("z", "189"),
        ]:
            with self.subTest(specifier=specifier):
                self.assertEqual(dateformat.format(my_birthday, specifier), expected)