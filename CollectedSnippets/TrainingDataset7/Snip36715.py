def test_months_edge(self):
        t = datetime.datetime(2022, 1, 1)
        tests = [
            (datetime.datetime(2022, 1, 31), "4\xa0weeks, 2\xa0days"),
            (datetime.datetime(2022, 2, 1), "1\xa0month"),
            (datetime.datetime(2022, 2, 28), "1\xa0month, 3\xa0weeks"),
            (datetime.datetime(2022, 3, 1), "2\xa0months"),
            (datetime.datetime(2022, 3, 31), "2\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 4, 1), "3\xa0months"),
            (datetime.datetime(2022, 4, 30), "3\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 5, 1), "4\xa0months"),
            (datetime.datetime(2022, 5, 31), "4\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 6, 1), "5\xa0months"),
            (datetime.datetime(2022, 6, 30), "5\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 7, 1), "6\xa0months"),
            (datetime.datetime(2022, 7, 31), "6\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 8, 1), "7\xa0months"),
            (datetime.datetime(2022, 8, 31), "7\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 9, 1), "8\xa0months"),
            (datetime.datetime(2022, 9, 30), "8\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 10, 1), "9\xa0months"),
            (datetime.datetime(2022, 10, 31), "9\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 11, 1), "10\xa0months"),
            (datetime.datetime(2022, 11, 30), "10\xa0months, 4\xa0weeks"),
            (datetime.datetime(2022, 12, 1), "11\xa0months"),
            (datetime.datetime(2022, 12, 31), "11\xa0months, 4\xa0weeks"),
        ]
        for value, expected in tests:
            with self.subTest():
                self.assertEqual(timesince(t, value), expected)