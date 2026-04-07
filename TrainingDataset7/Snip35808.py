def test_redirect_to_view_name(self):
        res = redirect("hardcoded2")
        self.assertEqual(res.url, "/hardcoded/doc.pdf")
        res = redirect("places", 1)
        self.assertEqual(res.url, "/places/1/")
        res = redirect("headlines", year="2008", month="02", day="17")
        self.assertEqual(res.url, "/headlines/2008.02.17/")
        with self.assertRaises(NoReverseMatch):
            redirect("not-a-view")