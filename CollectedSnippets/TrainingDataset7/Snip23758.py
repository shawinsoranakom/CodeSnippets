def test_get_object_custom_queryset(self):
        """
        Custom querysets are used when provided to
        BaseDateDetailView.get_object().
        """
        res = self.client.get(
            "/dates/books/get_object_custom_queryset/2006/may/01/%s/" % self.book2.pk
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.book2)
        self.assertEqual(res.context["book"], self.book2)
        self.assertTemplateUsed(res, "generic_views/book_detail.html")

        res = self.client.get(
            "/dates/books/get_object_custom_queryset/2008/oct/01/9999999/"
        )
        self.assertEqual(res.status_code, 404)