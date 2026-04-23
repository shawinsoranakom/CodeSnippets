def test_multiple_iterations(self):
        query = "SELECT * FROM raw_query_author"
        normal_authors = Author.objects.all()
        raw_authors = Author.objects.raw(query)

        # First Iteration
        first_iterations = 0
        for index, raw_author in enumerate(raw_authors):
            self.assertEqual(normal_authors[index], raw_author)
            first_iterations += 1

        # Second Iteration
        second_iterations = 0
        for index, raw_author in enumerate(raw_authors):
            self.assertEqual(normal_authors[index], raw_author)
            second_iterations += 1

        self.assertEqual(first_iterations, second_iterations)