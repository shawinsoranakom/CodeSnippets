def test_mutation_warning_text(self, show_error_details: bool):
        with testutil.patch_config_options(
            {"client.showErrorDetails": show_error_details}
        ):

            @st.cache
            def mutation_warning_func():
                return []

            a = mutation_warning_func()
            a.append("mutated!")
            mutation_warning_func()

            if show_error_details:
                el = self.get_delta_from_queue(-1).new_element
                self.assertEqual(el.exception.type, "CachedObjectMutationWarning")

                self.assertEqual(
                    normalize_md(el.exception.message),
                    normalize_md(
                        """
Return value of `mutation_warning_func()` was mutated between runs.

By default, Streamlit\'s cache should be treated as immutable, or it may behave
in unexpected ways. You received this warning because Streamlit detected that
an object returned by `mutation_warning_func()` was mutated outside of
`mutation_warning_func()`.

How to fix this:
* If you did not mean to mutate that return value:
  - If possible, inspect your code to find and remove that mutation.
  - Otherwise, you could also clone the returned value so you can freely
    mutate it.
* If you actually meant to mutate the return value and know the consequences of
doing so, annotate the function with `@st.cache(allow_output_mutation=True)`.

For more information and detailed solutions check out [our
documentation.](https://docs.streamlit.io/library/advanced-features/caching)
                    """
                    ),
                )
                self.assertNotEqual(len(el.exception.stack_trace), 0)
                self.assertEqual(el.exception.message_is_markdown, True)
                self.assertEqual(el.exception.is_warning, True)
            else:
                el = self.get_delta_from_queue(-1).new_element
                self.assertEqual(el.WhichOneof("type"), "exception")