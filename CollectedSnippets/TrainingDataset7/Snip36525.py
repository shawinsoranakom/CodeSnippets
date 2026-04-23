def test_iter(self):
        # Tests whether an object's custom `__iter__` method is being
        # used when iterating over it.

        class IterObject:
            def __init__(self, values):
                self.values = values

            def __iter__(self):
                return iter(self.values)

        original_list = ["test", "123"]
        self.assertEqual(list(self.lazy_wrap(IterObject(original_list))), original_list)