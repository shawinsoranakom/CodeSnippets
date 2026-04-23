def test_string(self):
        """Test st.write with a string."""
        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as p:
            st.write("some string")

            p.assert_called_once()

        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as p:
            st.write("more", "strings", "to", "pass")

            p.assert_called_once_with("more strings to pass", unsafe_allow_html=False)