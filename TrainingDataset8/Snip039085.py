def test_st_show(self):
        """Test st.experimental_show.

        Ideally we could test the order and content of the deltas.
        But not possible to inject a shared queue in `streamlit._with_dg()`

        Improvements:
        - verify markdown is escaped on write delta
        """
        thing = "something"

        with patch("streamlit.write") as write:
            with patch("streamlit.markdown") as markdown:
                st.experimental_show(thing)
                write.assert_called_once()
                markdown.assert_called_once()

        foo_show_bar = "baz"

        with patch("streamlit.write") as write:
            with patch("streamlit.markdown") as markdown:
                st.experimental_show(foo_show_bar)
                write.assert_called_once()
                markdown.assert_called_once()