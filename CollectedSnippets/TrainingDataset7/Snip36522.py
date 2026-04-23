def test_getitem(self):
        obj_list = self.lazy_wrap([1, 2, 3])
        obj_dict = self.lazy_wrap({"a": 1, "b": 2, "c": 3})

        self.assertEqual(obj_list[0], 1)
        self.assertEqual(obj_list[-1], 3)
        self.assertEqual(obj_list[1:2], [2])

        self.assertEqual(obj_dict["b"], 2)

        with self.assertRaises(IndexError):
            obj_list[3]

        with self.assertRaises(KeyError):
            obj_dict["f"]