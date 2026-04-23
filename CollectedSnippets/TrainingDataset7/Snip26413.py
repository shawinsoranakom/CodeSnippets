def test_get_related(self):
        self.assertEqual(self.a.reporter.id, self.r.id)
        # Article objects have access to their related Reporter objects.
        r = self.a.reporter
        self.assertEqual(r.id, self.r.id)