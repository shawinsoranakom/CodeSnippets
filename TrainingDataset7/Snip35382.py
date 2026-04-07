def test_allowed_database_chunked_cursor_queries(self):
        next(Car.objects.iterator(), None)