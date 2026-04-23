def test_deconstruct_child_with_path(self):
        obj = DeconstructibleWithPathChildClass("arg", key="value")
        path, args, kwargs = obj.deconstruct()
        self.assertEqual(
            path,
            "utils_tests.test_deconstruct.DeconstructibleWithPathChildClass",
        )
        self.assertEqual(args, ("arg",))
        self.assertEqual(kwargs, {"key": "value"})