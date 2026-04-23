def test_exception(self):
        """Test st.write that raises an exception."""
        # We patch streamlit.exception to observe it, but we also make sure
        # it's still called (via side_effect). This ensures that it's called
        # with the proper arguments.
        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as m, patch(
            "streamlit.delta_generator.DeltaGenerator.exception",
            side_effect=handle_uncaught_app_exception,
        ):
            m.side_effect = Exception("some exception")

            with self.assertRaises(Exception):
                st.write("some text")