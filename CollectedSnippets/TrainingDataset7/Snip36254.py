def test_deconstruct_with_path(self):
        obj = DeconstructibleWithPathClass("arg", key="value")
        path, args, kwargs = obj.deconstruct()
        self.assertEqual(
            path,
            "utils_tests.deconstructible_classes.DeconstructibleWithPathClass",
        )
        self.assertEqual(args, ("arg",))
        self.assertEqual(kwargs, {"key": "value"})