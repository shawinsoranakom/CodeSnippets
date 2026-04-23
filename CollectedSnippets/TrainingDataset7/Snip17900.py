def test_encode(self):
        msg = self.not_implemented_msg % "an encode"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.hasher.encode("password", "salt")