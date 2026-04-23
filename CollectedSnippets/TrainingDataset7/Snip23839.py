def test_verbose_name(self):
        res = self.client.get("/list/artists/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/list.html")
        self.assertEqual(list(res.context["object_list"]), list(Artist.objects.all()))
        self.assertIs(res.context["artist_list"], res.context["object_list"])
        self.assertIsNone(res.context["paginator"])
        self.assertIsNone(res.context["page_obj"])
        self.assertFalse(res.context["is_paginated"])