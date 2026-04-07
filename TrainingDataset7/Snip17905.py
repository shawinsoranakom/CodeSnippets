def test_verify(self):
        msg = self.not_implemented_msg % "a verify"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.hasher.verify("password", "encoded")