def test_dataframe_data(self):
        df = mock_data_frame()
        st._arrow_dataframe(df)

        proto = self.get_delta_from_queue().new_element.arrow_data_frame
        pd.testing.assert_frame_equal(bytes_to_data_frame(proto.data), df)