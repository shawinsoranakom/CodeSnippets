def test_missing_items(self):
        msg = (
            "AuthorList is missing a QuerySet. Define AuthorList.model, "
            "AuthorList.queryset, or override AuthorList.get_queryset()."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/list/authors/invalid/")