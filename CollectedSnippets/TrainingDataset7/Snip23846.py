def test_invalid_get_queryset(self):
        msg = (
            "AuthorListGetQuerysetReturnsNone requires either a 'template_name' "
            "attribute or a get_queryset() method that returns a QuerySet."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/list/authors/get_queryset/")