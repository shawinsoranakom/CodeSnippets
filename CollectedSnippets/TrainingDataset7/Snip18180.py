def test_save(self):
        with self.assertRaisesMessage(NotImplementedError, self.no_repr_msg):
            self.user.save()