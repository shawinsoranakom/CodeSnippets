def test_create(self):
        msg = self.not_implemented_msg % "a create"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.session.create()