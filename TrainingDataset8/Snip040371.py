def test_exception_type(self):
        """Test st.write with exception."""
        with patch("streamlit.delta_generator.DeltaGenerator.exception") as p:
            st.write(Exception("some exception"))

            p.assert_called_once()