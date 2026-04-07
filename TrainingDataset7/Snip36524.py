def test_delitem(self):
        obj_list = self.lazy_wrap([1, 2, 3])
        obj_dict = self.lazy_wrap({"a": 1, "b": 2, "c": 3})

        del obj_list[-1]
        del obj_dict["c"]
        self.assertEqual(obj_list, [1, 2])
        self.assertEqual(obj_dict, {"a": 1, "b": 2})

        with self.assertRaises(IndexError):
            del obj_list[3]

        with self.assertRaises(KeyError):
            del obj_dict["f"]