def test_parallel_count(self, *mocked_objects):
        result = self.get_parser().parse_args(["--parallel", "17"])
        self.assertEqual(result.parallel, 17)