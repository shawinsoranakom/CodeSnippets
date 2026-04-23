def test_protect_multiple(self):
        a = create_a("protect")
        b = B.objects.create(protect=a.protect)
        msg = (
            "Cannot delete some instances of model 'R' because they are "
            "referenced through protected foreign keys: 'A.protect', "
            "'B.protect'."
        )
        with self.assertRaisesMessage(ProtectedError, msg) as cm:
            a.protect.delete()
        self.assertEqual(cm.exception.protected_objects, {a, b})