def test_add_rows_rerun(self):
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        rq.enqueue(NEW_SESSION_MSG)

        # Simulate rerun
        for i in range(2):
            TEXT_DELTA_MSG1.metadata.delta_path[:] = make_delta_path(
                RootContainer.MAIN, (), 0
            )
            rq.enqueue(TEXT_DELTA_MSG1)

            DF_DELTA_MSG.metadata.delta_path[:] = make_delta_path(
                RootContainer.MAIN, (), 1
            )
            rq.enqueue(DF_DELTA_MSG)

            ADD_ROWS_MSG.metadata.delta_path[:] = make_delta_path(
                RootContainer.MAIN, (), 1
            )
            rq.enqueue(ADD_ROWS_MSG)

        queue = rq.flush()
        self.assertEqual(5, len(queue))

        # Text delta
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 0), queue[1].metadata.delta_path
        )
        self.assertEqual("text1", queue[1].delta.new_element.text.body)

        # Dataframe delta
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 1), queue[2].metadata.delta_path
        )
        col0 = queue[2].delta.new_element.data_frame.data.cols[0].int64s.data
        col1 = queue[2].delta.new_element.data_frame.data.cols[1].int64s.data
        self.assertEqual([0, 1, 2], col0)
        self.assertEqual([10, 11, 12], col1)

        # First add_rows delta
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 1), queue[3].metadata.delta_path
        )
        ar_col0 = queue[3].delta.add_rows.data.data.cols[0].int64s.data
        ar_col1 = queue[3].delta.add_rows.data.data.cols[1].int64s.data
        self.assertEqual([3, 4, 5], ar_col0)
        self.assertEqual([13, 14, 15], ar_col1)

        # Second add_rows delta
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 1), queue[4].metadata.delta_path
        )
        ar_col0 = queue[4].delta.add_rows.data.data.cols[0].int64s.data
        ar_col1 = queue[4].delta.add_rows.data.data.cols[1].int64s.data
        self.assertEqual([3, 4, 5], ar_col0)
        self.assertEqual([13, 14, 15], ar_col1)