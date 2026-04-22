def test_dict(self):
        """Test st.write with dict."""
        with patch("streamlit.delta_generator.DeltaGenerator.json") as p:
            st.write({"a": 1, "b": 2})

            p.assert_called_once()