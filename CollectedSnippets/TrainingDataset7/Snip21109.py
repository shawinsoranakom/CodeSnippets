def test_restrict_gfk_no_fast_delete(self):
        delete_top = DeleteTop.objects.create()
        generic_b1 = GenericB1.objects.create(generic_delete_top=delete_top)
        generic_b2 = GenericB2.objects.create(generic_delete_top=delete_top)
        generic_delete_bottom = GenericDeleteBottom.objects.create(
            generic_b1=generic_b1,
            generic_b2=generic_b2,
        )
        msg = (
            "Cannot delete some instances of model 'GenericB1' because they "
            "are referenced through restricted foreign keys: "
            "'GenericDeleteBottom.generic_b1'."
        )
        with self.assertRaisesMessage(RestrictedError, msg) as cm:
            generic_b1.delete()
        self.assertEqual(cm.exception.restricted_objects, {generic_delete_bottom})
        self.assertTrue(DeleteTop.objects.exists())
        self.assertTrue(GenericB1.objects.exists())
        self.assertTrue(GenericB2.objects.exists())
        self.assertTrue(GenericDeleteBottom.objects.exists())
        # Object referenced also with CASCADE relationship can be deleted.
        delete_top.delete()
        self.assertFalse(DeleteTop.objects.exists())
        self.assertFalse(GenericB1.objects.exists())
        self.assertFalse(GenericB2.objects.exists())
        self.assertFalse(GenericDeleteBottom.objects.exists())