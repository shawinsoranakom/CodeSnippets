def test_futuredates(self):
        the_future = datetime(2100, 10, 25, 0, 00)
        self.assertEqual(dateformat.format(the_future, r"Y"), "2100")