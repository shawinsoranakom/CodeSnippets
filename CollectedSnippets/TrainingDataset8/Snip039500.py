def test_st_warning_text(self):
        @st.cache
        def st_warning_text_func():
            st.markdown("hi")

        st_warning_text_func()

        el = self.get_delta_from_queue(-2).new_element
        self.assertEqual(el.exception.type, "CachedStFunctionWarning")
        self.assertEqual(
            normalize_md(el.exception.message),
            normalize_md(
                """
Your script uses `st.markdown()` or `st.write()` to write to your Streamlit app
from within some cached code at `st_warning_text_func()`. This code will only be
called when we detect a cache "miss", which can lead to unexpected results.

How to fix this:
* Move the `st.markdown()` or `st.write()` call outside `st_warning_text_func()`.
* Or, if you know what you're doing, use `@st.cache(suppress_st_warning=True)`
to suppress the warning.
        """
            ),
        )
        self.assertNotEqual(len(el.exception.stack_trace), 0)
        self.assertEqual(el.exception.message_is_markdown, True)
        self.assertEqual(el.exception.is_warning, True)

        el = self.get_delta_from_queue(-1).new_element
        self.assertEqual(el.markdown.body, "hi")