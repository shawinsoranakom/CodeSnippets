def test_add_existing_different_type(self):
        # A single SELECT query is necessary to compare existing values to the
        # provided one; no INSERT should be attempted.
        with self.assertNumQueries(1):
            self.a1.publications.add(str(self.p1.pk))
        self.assertEqual(self.a1.publications.get(), self.p1)