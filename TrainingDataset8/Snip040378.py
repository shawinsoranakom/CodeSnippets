def test_namedtuple(self):
        """Test st.write with list."""
        with patch("streamlit.delta_generator.DeltaGenerator.json") as p:
            Boy = namedtuple("Boy", ("name", "age"))
            John = Boy("John", 29)
            st.write(John)

            p.assert_called_once()