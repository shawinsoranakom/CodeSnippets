def test_force_insert_diamond_mti(self):
        # Force insert all parents.
        with self.assertNumQueries(4):
            DiamondSubSubCounter(pk=1, value=1).save(
                force_insert=(Counter, SubCounter, OtherSubCounter)
            )
        with self.assertNumQueries(4):
            DiamondSubSubCounter(pk=2, value=1).save(force_insert=(models.Model,))
        # Force insert parents, and don't force insert a common grandparent.
        with self.assertNumQueries(5):
            DiamondSubSubCounter(pk=3, value=1).save(
                force_insert=(SubCounter, OtherSubCounter)
            )
        grandparent = Counter.objects.create(pk=4, value=1)
        with self.assertNumQueries(4):
            DiamondSubSubCounter(pk=grandparent.pk, value=1).save(
                force_insert=(SubCounter, OtherSubCounter),
            )
        # Force insert all parents, grandparent conflicts.
        grandparent = Counter.objects.create(pk=5, value=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DiamondSubSubCounter(pk=grandparent.pk, value=1).save(
                force_insert=(models.Model,)
            )