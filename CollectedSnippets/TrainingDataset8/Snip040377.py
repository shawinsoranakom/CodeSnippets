def test_list(self):
        """Test st.write with list."""
        with patch("streamlit.delta_generator.DeltaGenerator.json") as p:
            st.write([1, 2, 3])

            p.assert_called_once()