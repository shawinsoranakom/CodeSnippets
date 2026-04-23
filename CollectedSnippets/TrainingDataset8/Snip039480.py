def assert_deltas(container: int, path: Tuple[int, ...], idx: int):
            # Text delta
            self.assertEqual(
                make_delta_path(container, path, 0), queue[idx].metadata.delta_path
            )
            self.assertEqual("text1", queue[idx].delta.new_element.text.body)

            # Dataframe delta
            self.assertEqual(
                make_delta_path(container, path, 1), queue[idx + 1].metadata.delta_path
            )
            col0 = queue[idx + 1].delta.new_element.data_frame.data.cols[0].int64s.data
            col1 = queue[idx + 1].delta.new_element.data_frame.data.cols[1].int64s.data
            self.assertEqual([0, 1, 2], col0)
            self.assertEqual([10, 11, 12], col1)

            # add_rows delta
            self.assertEqual(
                make_delta_path(container, path, 1), queue[idx + 2].metadata.delta_path
            )
            ar_col0 = queue[idx + 2].delta.add_rows.data.data.cols[0].int64s.data
            ar_col1 = queue[idx + 2].delta.add_rows.data.data.cols[1].int64s.data
            self.assertEqual([3, 4, 5], ar_col0)
            self.assertEqual([13, 14, 15], ar_col1)