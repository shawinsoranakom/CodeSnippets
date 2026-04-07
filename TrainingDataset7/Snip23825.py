def test_items(self):
        res = self.client.get("/list/dict/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/list.html")
        self.assertEqual(res.context["object_list"][0]["first"], "John")