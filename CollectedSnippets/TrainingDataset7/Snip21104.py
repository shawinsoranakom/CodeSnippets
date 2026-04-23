def test_restrict(self):
        a = create_a("restrict")
        msg = (
            "Cannot delete some instances of model 'R' because they are "
            "referenced through restricted foreign keys: 'A.restrict'."
        )
        with self.assertRaisesMessage(RestrictedError, msg) as cm:
            a.restrict.delete()
        self.assertEqual(cm.exception.restricted_objects, {a})