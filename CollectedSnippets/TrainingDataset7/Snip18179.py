def test_delete(self):
        with self.assertRaisesMessage(NotImplementedError, self.no_repr_msg):
            self.user.delete()