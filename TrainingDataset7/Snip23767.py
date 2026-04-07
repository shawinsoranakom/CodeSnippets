def test_detail_by_custom_pk(self):
        res = self.client.get("/detail/author/bycustompk/%s/" % self.author1.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author1)
        self.assertEqual(res.context["author"], self.author1)
        self.assertTemplateUsed(res, "generic_views/author_detail.html")