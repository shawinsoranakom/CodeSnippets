def test_class(self):
        """Test st.write with a class."""

        class SomeClass(object):
            pass

        with patch("streamlit.delta_generator.DeltaGenerator.text") as p:
            st.write(SomeClass)

            p.assert_called_once_with(SomeClass)

        with patch("streamlit.delta_generator.DeltaGenerator.text") as p:
            empty_df = pd.DataFrame()
            st.write(type(empty_df))

            p.assert_called_once_with(type(empty_df))