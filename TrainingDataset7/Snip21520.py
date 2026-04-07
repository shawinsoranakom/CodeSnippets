def test_or(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            Combinable() | Combinable()