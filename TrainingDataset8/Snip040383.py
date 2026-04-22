def test_default_object(self):
        """Test st.write with default clause ie some object."""

        class SomeObject(object):
            def __str__(self):
                return "1 * 2 - 3 = 4 `ok` !"

        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as p:
            st.write(SomeObject())

            p.assert_called_once_with(
                "`1 * 2 - 3 = 4 \\`ok\\` !`", unsafe_allow_html=False
            )