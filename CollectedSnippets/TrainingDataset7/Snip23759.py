def test_get_object_custom_queryset_numqueries(self):
        with self.assertNumQueries(1):
            self.client.get("/dates/books/get_object_custom_queryset/2006/may/01/2/")