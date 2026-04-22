def test_reduce_not_hashable(self):
        class A:
            def __init__(self):
                self.x = [1, 2, 3]

        with self.assertRaises(UnhashableTypeError):
            get_hash(A().__reduce__())