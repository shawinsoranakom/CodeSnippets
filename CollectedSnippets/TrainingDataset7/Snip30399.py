def test_unspecified_unsaved_parent(self):
        parent = RelatedObject.objects.create()
        parent.single = SingleObject()
        parent.f = 42
        RelatedObject.objects.bulk_update([parent], fields=["f"])
        parent.refresh_from_db()
        self.assertEqual(parent.f, 42)
        self.assertIsNone(parent.single)