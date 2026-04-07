def test_pagination_page_range(self):
        """
        Regression tests for ticket #15653: ensure the number of pages
        generated for changelist views are correct.
        """
        # instantiating and setting up ChangeList object
        m = GroupAdmin(Group, custom_site)
        request = self.factory.get("/group/")
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        cl.list_per_page = 10

        ELLIPSIS = cl.paginator.ELLIPSIS
        for number, pages, expected in [
            (1, 1, []),
            (1, 2, [1, 2]),
            (6, 11, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            (6, 12, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
            (6, 13, [1, 2, 3, 4, 5, 6, 7, 8, 9, ELLIPSIS, 12, 13]),
            (7, 12, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
            (7, 13, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]),
            (7, 14, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ELLIPSIS, 13, 14]),
            (8, 13, [1, 2, ELLIPSIS, 5, 6, 7, 8, 9, 10, 11, 12, 13]),
            (8, 14, [1, 2, ELLIPSIS, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]),
            (8, 15, [1, 2, ELLIPSIS, 5, 6, 7, 8, 9, 10, 11, ELLIPSIS, 14, 15]),
        ]:
            with self.subTest(number=number, pages=pages):
                # assuming exactly `pages * cl.list_per_page` objects
                Group.objects.all().delete()
                for i in range(pages * cl.list_per_page):
                    Group.objects.create(name="test band")

                # setting page number and calculating page range
                cl.page_num = number
                cl.get_results(request)
                self.assertEqual(list(pagination(cl)["page_range"]), expected)