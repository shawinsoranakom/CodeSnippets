def test_invalid_queryset(self):
        msg = (
            "AuthorDetail is missing a QuerySet. Define AuthorDetail.model, "
            "AuthorDetail.queryset, or override AuthorDetail.get_queryset()."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/detail/author/invalid/qs/")