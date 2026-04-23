def test_force_insert_with_grandparent(self):
        with self.assertNumQueries(4):
            SubSubCounter(pk=1, value=1).save(force_insert=True)
        # Force insert parents on all levels and don't UPDATE first.
        with self.assertNumQueries(3):
            SubSubCounter(pk=2, value=1).save(force_insert=(models.Model,))
        with self.assertNumQueries(3):
            SubSubCounter(pk=3, value=1).save(force_insert=(Counter,))
        # Force insert only the last parent.
        with self.assertNumQueries(4):
            SubSubCounter(pk=4, value=1).save(force_insert=(SubCounter,))