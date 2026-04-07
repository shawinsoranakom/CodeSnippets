def test_created_via_related_set(self):
        self.assertEqual(self.a2.reporter.id, self.r.id)