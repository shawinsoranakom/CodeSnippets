def test_set_password(self):
        with self.assertRaisesMessage(NotImplementedError, self.no_repr_msg):
            self.user.set_password("password")