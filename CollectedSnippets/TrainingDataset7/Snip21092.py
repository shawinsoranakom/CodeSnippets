def test_protect(self):
        a = create_a("protect")
        msg = (
            "Cannot delete some instances of model 'R' because they are "
            "referenced through protected foreign keys: 'A.protect'."
        )
        with self.assertRaisesMessage(ProtectedError, msg) as cm:
            a.protect.delete()
        self.assertEqual(cm.exception.protected_objects, {a})