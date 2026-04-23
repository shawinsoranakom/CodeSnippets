def _get_message(self, orig_exc):
        return (
            """
Return value of %(func_name)s was mutated between runs.

By default, Streamlit's cache should be treated as immutable, or it may behave
in unexpected ways. You received this warning because Streamlit detected
that an object returned by %(func_name)s was mutated outside of %(func_name)s.

How to fix this:
* If you did not mean to mutate that return value:
  - If possible, inspect your code to find and remove that mutation.
  - Otherwise, you could also clone the returned value so you can freely
    mutate it.
* If you actually meant to mutate the return value and know the consequences of
doing so, annotate the function with `@st.cache(allow_output_mutation=True)`.

For more information and detailed solutions check out [our documentation.]
(https://docs.streamlit.io/library/advanced-features/caching)
            """
            % {"func_name": orig_exc.cached_func_name}
        ).strip("\n")