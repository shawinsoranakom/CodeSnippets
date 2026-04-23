def test_st_arrow_dataframe(self):
        """Test st._arrow_dataframe."""
        from streamlit.type_util import bytes_to_data_frame

        df = pd.DataFrame({"one": [1, 2], "two": [11, 22]})

        st._arrow_dataframe(df)

        proto = self.get_delta_from_queue().new_element.arrow_data_frame
        pd.testing.assert_frame_equal(bytes_to_data_frame(proto.data), df)