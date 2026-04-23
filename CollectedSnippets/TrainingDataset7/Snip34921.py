def test_parallel_default(self, *mocked_objects):
        result = self.get_parser().parse_args([])
        self.assertEqual(result.parallel, 0)