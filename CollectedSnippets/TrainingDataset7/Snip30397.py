def test_nullable_fk_after_related_save(self):
        parent = RelatedObject.objects.create()
        child = SingleObject()
        parent.single = child
        parent.single.save()
        RelatedObject.objects.bulk_update([parent], fields=["single"])
        self.assertEqual(parent.single_id, parent.single.pk)
        parent.refresh_from_db()
        self.assertEqual(parent.single, child)