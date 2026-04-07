def test_force_insert_not_base(self):
        msg = "Invalid force_insert member. SubCounter must be a base of Counter."
        with self.assertRaisesMessage(TypeError, msg):
            Counter().save(force_insert=(SubCounter,))