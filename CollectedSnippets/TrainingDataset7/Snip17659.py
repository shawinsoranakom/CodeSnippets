def test_iter(self):
        with self.assertRaisesMessage(TypeError, "PermWrapper is not iterable."):
            iter(PermWrapper(MockUser()))