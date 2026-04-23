def _do_test(self, fn, expectedWidth, expectedHeight):
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5]})

        fn(st._arrow_dataframe, df)
        arrow_data_frame = self.get_delta_from_queue().new_element.arrow_data_frame
        self.assertEqual(arrow_data_frame.width, expectedWidth)
        self.assertEqual(arrow_data_frame.height, expectedHeight)