def check_indexes(self, params, page_num, indexes):
        """
        Helper method that instantiates a Paginator object from the passed
        params and then checks that the start and end indexes of the passed
        page_num match those given as a 2-tuple in indexes.
        """
        paginator = Paginator(*params)
        if page_num == "first":
            page_num = 1
        elif page_num == "last":
            page_num = paginator.num_pages
        page = paginator.page(page_num)
        start, end = indexes
        msg = "For %s of page %s, expected %s but got %s. Paginator parameters were: %s"
        self.assertEqual(
            start,
            page.start_index(),
            msg % ("start index", page_num, start, page.start_index(), params),
        )
        self.assertEqual(
            end,
            page.end_index(),
            msg % ("end index", page_num, end, page.end_index(), params),
        )