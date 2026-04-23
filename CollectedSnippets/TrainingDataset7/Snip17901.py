def test_decode(self):
        msg = self.not_implemented_msg % "a decode"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.hasher.decode("encoded")