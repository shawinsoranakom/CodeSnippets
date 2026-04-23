def test_empty_object_list(self):
        deserializer = Deserializer(object_list=[])
        with self.assertRaises(StopIteration):
            next(deserializer)