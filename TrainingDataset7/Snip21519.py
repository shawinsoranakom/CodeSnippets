def test_and(self):
        with self.assertRaisesMessage(NotImplementedError, self.bitwise_msg):
            Combinable() & Combinable()