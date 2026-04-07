def test_time_formats(self):
        # Specifiers 'I', 'r', and 'U' are covered in test_timezones().
        my_birthday = datetime(1979, 7, 8, 22, 00)
        for specifier, expected in [
            ("a", "p.m."),
            ("A", "PM"),
            ("f", "10"),
            ("g", "10"),
            ("G", "22"),
            ("h", "10"),
            ("H", "22"),
            ("i", "00"),
            ("P", "10 p.m."),
            ("s", "00"),
            ("u", "000000"),
        ]:
            with self.subTest(specifier=specifier):
                self.assertEqual(dateformat.format(my_birthday, specifier), expected)