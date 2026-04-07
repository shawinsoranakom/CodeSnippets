def test_verbose_name(self):
        res = self.client.get("/detail/artist/%s/" % self.artist1.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.artist1)
        self.assertEqual(res.context["artist"], self.artist1)
        self.assertTemplateUsed(res, "generic_views/artist_detail.html")