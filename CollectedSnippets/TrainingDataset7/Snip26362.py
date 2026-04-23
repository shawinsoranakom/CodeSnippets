def test_get(self):
        # Article objects have access to their related Reporter objects.
        r = self.a.reporter
        self.assertEqual(r.id, self.r.id)
        self.assertEqual((r.first_name, self.r.last_name), ("John", "Smith"))