def test_empty_format(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, ""), "")