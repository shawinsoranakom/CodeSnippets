def test_context_object_name(self):
        res = self.client.get(
            "/detail/author/%s/context_object_name/" % self.author1.pk
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author1)
        self.assertEqual(res.context["thingy"], self.author1)
        self.assertNotIn("author", res.context)
        self.assertTemplateUsed(res, "generic_views/author_detail.html")