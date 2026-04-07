def test_force_insert_parent(self):
        with self.assertNumQueries(3):
            SubCounter(pk=1, value=1).save(force_insert=True)
        # Force insert a new parent and don't UPDATE first.
        with self.assertNumQueries(2):
            SubCounter(pk=2, value=1).save(force_insert=(Counter,))
        with self.assertNumQueries(2):
            SubCounter(pk=3, value=1).save(force_insert=(models.Model,))