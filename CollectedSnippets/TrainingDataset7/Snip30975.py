def test_escaped_percent(self):
        query = "SELECT * FROM raw_query_author WHERE first_name like 'J%%'"
        qset = Author.objects.raw(query)
        self.assertEqual(len(qset), 2)