def test_reversed_and(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            object() & Combinable()