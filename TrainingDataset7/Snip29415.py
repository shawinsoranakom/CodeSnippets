def test_get_page(self):
        """
        Paginator.get_page() returns a valid page even with invalid page
        arguments.
        """
        paginator = Paginator([1, 2, 3], 2)
        page = paginator.get_page(1)
        self.assertEqual(page.number, 1)
        self.assertEqual(page.object_list, [1, 2])
        # An empty page returns the last page.
        self.assertEqual(paginator.get_page(3).number, 2)
        # Non-integer page returns the first page.
        self.assertEqual(paginator.get_page(None).number, 1)