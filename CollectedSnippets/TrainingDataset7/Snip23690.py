def test_empty_archive_view(self):
        Book.objects.all().delete()
        res = self.client.get("/dates/books/")
        self.assertEqual(res.status_code, 404)