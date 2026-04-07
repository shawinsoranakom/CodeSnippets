def test_each_context(self):
        ctx = self.ctx
        self.assertEqual(ctx["site_header"], "Django administration")
        self.assertEqual(ctx["site_title"], "Django site admin")
        self.assertEqual(ctx["site_url"], "/")
        self.assertIs(ctx["has_permission"], True)