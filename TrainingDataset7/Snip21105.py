def test_restrict_multiple(self):
        a = create_a("restrict")
        b3 = B3.objects.create(restrict=a.restrict)
        msg = (
            "Cannot delete some instances of model 'R' because they are "
            "referenced through restricted foreign keys: 'A.restrict', "
            "'B3.restrict'."
        )
        with self.assertRaisesMessage(RestrictedError, msg) as cm:
            a.restrict.delete()
        self.assertEqual(cm.exception.restricted_objects, {a, b3})