def _do_test(self, fn, expectedWidth, expectedHeight):
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5]})

        fn(st._legacy_dataframe, df)
        metadata = self._get_metadata()
        self.assertEqual(metadata.element_dimension_spec.width, expectedWidth)
        self.assertEqual(metadata.element_dimension_spec.height, expectedHeight)