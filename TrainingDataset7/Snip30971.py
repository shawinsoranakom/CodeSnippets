def test_order_handler(self):
        """Raw query tolerates columns being returned in any order."""
        selects = (
            ("dob, last_name, first_name, id"),
            ("last_name, dob, first_name, id"),
            ("first_name, last_name, dob, id"),
        )

        for select in selects:
            query = "SELECT %s FROM raw_query_author" % select
            authors = Author.objects.all()
            self.assertSuccessfulRawQuery(Author, query, authors)