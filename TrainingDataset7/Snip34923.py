def test_parallel_auto(self, *mocked_objects):
        result = self.get_parser().parse_args(["--parallel", "auto"])
        self.assertEqual(result.parallel, "auto")