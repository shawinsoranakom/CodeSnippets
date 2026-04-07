def test_reversed_or(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            object() | Combinable()