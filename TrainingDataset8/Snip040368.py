def test_repr_html(self):
        """Test st.write with an object that defines _repr_html_."""

        class FakeHTMLable(object):
            def _repr_html_(self):
                return "<strong>hello world</strong>"

        with patch("streamlit.delta_generator.DeltaGenerator.markdown") as p:
            st.write(FakeHTMLable())

            p.assert_called_once_with(
                "<strong>hello world</strong>", unsafe_allow_html=True
            )