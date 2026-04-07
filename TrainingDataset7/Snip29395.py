def test_orphans_value_larger_than_per_page_value(self):
        # RemovedInDjango70Warning: When the deprecation ends, replace with:
        # msg = (
        #     "The orphans argument cannot be larger than or equal to the "
        #     "per_page argument."
        # )
        msg = (
            "Support for the orphans argument being larger than or equal to the "
            "per_page argument is deprecated. This will raise a ValueError in "
            "Django 7.0."
        )
        for paginator_class in [Paginator, AsyncPaginator]:
            for orphans in [2, 3]:
                with self.subTest(paginator_class=paginator_class, msg=msg):
                    # RemovedInDjango70Warning: When the deprecation ends,
                    # replace with:
                    # with self.assertRaisesMessage(ValueError, msg):
                    with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
                        paginator_class([1, 2, 3], 2, orphans)