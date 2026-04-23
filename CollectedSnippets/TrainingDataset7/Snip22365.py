def test_force_insert_with_existing_grandparent(self):
        # Force insert only the last child.
        grandparent = Counter.objects.create(pk=1, value=1)
        with self.assertNumQueries(4):
            SubSubCounter(pk=grandparent.pk, value=1).save(force_insert=True)
        # Force insert a parent, and don't force insert a grandparent.
        grandparent = Counter.objects.create(pk=2, value=1)
        with self.assertNumQueries(3):
            SubSubCounter(pk=grandparent.pk, value=1).save(force_insert=(SubCounter,))
        # Force insert parents on all levels, grandparent conflicts.
        grandparent = Counter.objects.create(pk=3, value=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SubSubCounter(pk=grandparent.pk, value=1).save(force_insert=(Counter,))