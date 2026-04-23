def test_simple_object(self):
        res = self.client.get("/detail/obj/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], {"foo": "bar"})
        self.assertIsInstance(res.context["view"], View)
        self.assertTemplateUsed(res, "generic_views/detail.html")