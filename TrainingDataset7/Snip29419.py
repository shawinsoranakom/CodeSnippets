def test_get_page_empty_object_list_and_allow_empty_first_page_false(self):
        """
        Paginator.get_page() raises EmptyPage if allow_empty_first_page=False
        and object_list is empty.
        """
        paginator = Paginator([], 2, allow_empty_first_page=False)
        with self.assertRaises(EmptyPage):
            paginator.get_page(1)