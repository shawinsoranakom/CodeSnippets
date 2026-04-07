def test_restrict_path_cascade_indirect_diamond(self):
        delete_top = DeleteTop.objects.create()
        b1 = B1.objects.create(delete_top=delete_top)
        b2 = B2.objects.create(delete_top=delete_top)
        delete_bottom = DeleteBottom.objects.create(b1=b1, b2=b2)
        msg = (
            "Cannot delete some instances of model 'B1' because they are "
            "referenced through restricted foreign keys: 'DeleteBottom.b1'."
        )
        with self.assertRaisesMessage(RestrictedError, msg) as cm:
            b1.delete()
        self.assertEqual(cm.exception.restricted_objects, {delete_bottom})
        self.assertTrue(DeleteTop.objects.exists())
        self.assertTrue(B1.objects.exists())
        self.assertTrue(B2.objects.exists())
        self.assertTrue(DeleteBottom.objects.exists())
        # Object referenced also with CASCADE relationship can be deleted.
        delete_top.delete()
        self.assertFalse(DeleteTop.objects.exists())
        self.assertFalse(B1.objects.exists())
        self.assertFalse(B2.objects.exists())
        self.assertFalse(DeleteBottom.objects.exists())