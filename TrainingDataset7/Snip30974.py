def test_params_none(self):
        query = "SELECT * FROM raw_query_author WHERE first_name like 'J%'"
        qset = Author.objects.raw(query, params=None)
        self.assertEqual(len(qset), 2)