def test_help(self):
        """Test st.write with help types."""
        # Test module
        with patch("streamlit.delta_generator.DeltaGenerator.help") as p:
            st.write(np)

            p.assert_called_once()

        # Test function
        with patch("streamlit.delta_generator.DeltaGenerator.help") as p:
            st.write(st.set_option)

            p.assert_called_once()