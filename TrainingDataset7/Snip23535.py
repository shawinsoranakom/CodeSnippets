def test_generic_relation_to_inherited_child(self):
        # GenericRelations to models that use multi-table inheritance work.
        granite = ValuableRock.objects.create(name="granite", hardness=5)
        ValuableTaggedItem.objects.create(
            content_object=granite, tag="countertop", value=1
        )
        self.assertEqual(ValuableRock.objects.filter(tags__value=1).count(), 1)
        # We're generating a slightly inefficient query for tags__tag - we
        # first join ValuableRock -> TaggedItem -> ValuableTaggedItem, and then
        # we fetch tag by joining TaggedItem from ValuableTaggedItem. The last
        # join isn't necessary, as TaggedItem <-> ValuableTaggedItem is a
        # one-to-one join.
        self.assertEqual(ValuableRock.objects.filter(tags__tag="countertop").count(), 1)
        granite.delete()  # deleting the rock should delete the related tag.
        self.assertEqual(ValuableTaggedItem.objects.count(), 0)