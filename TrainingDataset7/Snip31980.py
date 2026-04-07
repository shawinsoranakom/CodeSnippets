def test_delete(self):
        msg = self.not_implemented_msg % "a delete"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.session.delete()