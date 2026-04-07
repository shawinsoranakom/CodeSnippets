def test_restrict_path_cascade_indirect(self):
        a = create_a("restrict")
        a.restrict.p = P.objects.create()
        a.restrict.save()
        msg = (
            "Cannot delete some instances of model 'P' because they are "
            "referenced through restricted foreign keys: 'A.restrict'."
        )
        with self.assertRaisesMessage(RestrictedError, msg) as cm:
            a.restrict.p.delete()
        self.assertEqual(cm.exception.restricted_objects, {a})
        # Object referenced also with CASCADE relationship can be deleted.
        a.cascade.p = a.restrict.p
        a.cascade.save()
        a.restrict.p.delete()
        self.assertFalse(A.objects.filter(name="restrict").exists())
        self.assertFalse(R.objects.filter(pk=a.restrict_id).exists())