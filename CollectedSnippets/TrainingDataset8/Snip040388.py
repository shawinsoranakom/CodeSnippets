def test_sidebar(self):
        """Test st.write in the sidebar."""
        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as m, patch(
            "streamlit.delta_generator.DeltaGenerator.help"
        ) as h:
            st.sidebar.write("markdown", st.help)

            m.assert_called_once()
            h.assert_called_once()