def test_st_video_other_inputs(self):
        """Test that our other data types don't result in an error."""
        st.video(b"bytes_data")
        st.video("str_data".encode("utf-8"))
        st.video(BytesIO(b"bytesio_data"))
        st.video(np.array([0, 1, 2, 3]))