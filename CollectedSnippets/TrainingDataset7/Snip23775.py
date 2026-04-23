def test_template_name(self):
        res = self.client.get("/detail/author/%s/template_name/" % self.author1.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author1)
        self.assertEqual(res.context["author"], self.author1)
        self.assertTemplateUsed(res, "generic_views/about.html")