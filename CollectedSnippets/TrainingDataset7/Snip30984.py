def test_annotations(self):
        query = (
            "SELECT a.*, count(b.id) as book_count "
            "FROM raw_query_author a "
            "LEFT JOIN raw_query_book b ON a.id = b.author_id "
            "GROUP BY a.id, a.first_name, a.last_name, a.dob ORDER BY a.id"
        )
        expected_annotations = (
            ("book_count", 3),
            ("book_count", 0),
            ("book_count", 1),
            ("book_count", 0),
        )
        authors = Author.objects.order_by("pk")
        self.assertSuccessfulRawQuery(Author, query, authors, expected_annotations)