def test_check_password(self):
        with self.assertRaisesMessage(NotImplementedError, self.no_repr_msg):
            self.user.check_password("password")