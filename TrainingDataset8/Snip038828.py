def test_strip_streamlit_stack_entries(self):
        """Test that StreamlitAPIExceptions don't include Streamlit entries
        in the stack trace.

        """
        # Create a StreamlitAPIException.
        err = None
        try:
            st.image("http://not_an_image.png", width=-1)
        except StreamlitAPIException as e:
            err = e
        self.assertIsNotNone(err)

        # Marshall it.
        proto = ExceptionProto()
        exception.marshall(proto, err)

        # The streamlit package should not appear in any stack entry.
        streamlit_dir = os.path.dirname(st.__file__)
        streamlit_dir = os.path.join(os.path.realpath(streamlit_dir), "")
        for line in proto.stack_trace:
            self.assertNotIn(streamlit_dir, line, "Streamlit stack entry not stripped")