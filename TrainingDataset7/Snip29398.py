def test_no_content_allow_empty_first_page(self):
        # With no content and allow_empty_first_page=True, 1 is a valid page.
        paginator = Paginator([], 2)
        self.assertEqual(paginator.validate_number(1), 1)