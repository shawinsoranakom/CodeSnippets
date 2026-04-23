def test_xor(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            Combinable() ^ Combinable()