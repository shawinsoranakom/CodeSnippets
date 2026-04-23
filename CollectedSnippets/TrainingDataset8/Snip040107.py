def test_st_arrow_table(self):
        """Test st._arrow_table."""
        from streamlit.type_util import bytes_to_data_frame

        df = pd.DataFrame([[1, 2], [3, 4]], columns=["col1", "col2"])

        st._arrow_table(df)

        proto = self.get_delta_from_queue().new_element.arrow_table
        pd.testing.assert_frame_equal(bytes_to_data_frame(proto.data), df)