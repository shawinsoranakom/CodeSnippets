def test_protect_path(self):
        a = create_a("protect")
        a.protect.p = P.objects.create()
        a.protect.save()
        msg = (
            "Cannot delete some instances of model 'P' because they are "
            "referenced through protected foreign keys: 'R.p'."
        )
        with self.assertRaisesMessage(ProtectedError, msg) as cm:
            a.protect.p.delete()
        self.assertEqual(cm.exception.protected_objects, {a})