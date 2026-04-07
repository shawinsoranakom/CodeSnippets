def test_reversed_xor(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            object() ^ Combinable()