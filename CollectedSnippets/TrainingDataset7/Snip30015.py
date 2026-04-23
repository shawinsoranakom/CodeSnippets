def test_from_parameter(self):
        self.assertIsNone(SearchConfig.from_parameter(None))
        self.assertEqual(SearchConfig.from_parameter("foo"), SearchConfig("foo"))
        self.assertEqual(
            SearchConfig.from_parameter(SearchConfig("bar")), SearchConfig("bar")
        )