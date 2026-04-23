def test_session_state(self):
        """Test st.write with st.session_state."""
        with patch("streamlit.delta_generator.DeltaGenerator.json") as p:
            st.write(SessionStateProxy())

            p.assert_called_once()