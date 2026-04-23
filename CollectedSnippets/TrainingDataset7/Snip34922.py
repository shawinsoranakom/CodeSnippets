def test_parallel_flag(self, *mocked_objects):
        result = self.get_parser().parse_args(["--parallel"])
        self.assertEqual(result.parallel, "auto")