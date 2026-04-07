def test_deconstruct_child(self):
        obj = DeconstructibleChildClass("arg", key="value")
        path, args, kwargs = obj.deconstruct()
        self.assertEqual(path, "utils_tests.test_deconstruct.DeconstructibleChildClass")
        self.assertEqual(args, ("arg",))
        self.assertEqual(kwargs, {"key": "value"})