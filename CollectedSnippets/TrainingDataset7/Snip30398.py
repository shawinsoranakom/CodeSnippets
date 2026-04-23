def test_unsaved_parent(self):
        parent = RelatedObject.objects.create()
        parent.single = SingleObject()
        msg = (
            "bulk_update() prohibited to prevent data loss due to unsaved "
            "related object 'single'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            RelatedObject.objects.bulk_update([parent], fields=["single"])