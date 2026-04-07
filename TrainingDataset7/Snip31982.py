def test_exists(self):
        msg = self.not_implemented_msg % "an exists"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.session.exists(None)