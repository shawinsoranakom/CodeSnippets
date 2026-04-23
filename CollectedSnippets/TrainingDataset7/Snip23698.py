def test_no_duplicate_query(self):
        # Regression test for #18354
        with self.assertNumQueries(2):
            self.client.get("/dates/books/reverse/")