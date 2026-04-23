def test_page_indexes(self):
        """
        Paginator pages have the correct start and end indexes.
        """
        tests = self.get_test_cases_for_test_page_indexes()
        for params, first, last in tests:
            self.check_indexes(params, "first", first)
            self.check_indexes(params, "last", last)

        # When no items and no empty first page, we should get EmptyPage error.
        with self.assertRaises(EmptyPage):
            self.check_indexes(([], 4, 0, False), 1, None)
        with self.assertRaises(EmptyPage):
            self.check_indexes(([], 4, 1, False), 1, None)
        with self.assertRaises(EmptyPage):
            self.check_indexes(([], 4, 2, False), 1, None)