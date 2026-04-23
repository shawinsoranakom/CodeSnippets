def test_dateformat(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, r"Y z \C\E\T"), "1979 189 CET")

        self.assertEqual(dateformat.format(my_birthday, r"jS \o\f F"), "8th of July")