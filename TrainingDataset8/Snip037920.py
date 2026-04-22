def _get_message(self, st_func_name, cached_func):
        args = {
            "st_func_name": "`st.%s()` or `st.write()`" % st_func_name,
            "func_name": _get_cached_func_name_md(cached_func),
        }

        return (
            """
Your script uses %(st_func_name)s to write to your Streamlit app from within
some cached code at %(func_name)s. This code will only be called when we detect
a cache "miss", which can lead to unexpected results.

How to fix this:
* Move the %(st_func_name)s call outside %(func_name)s.
* Or, if you know what you're doing, use `@st.cache(suppress_st_warning=True)`
to suppress the warning.
            """
            % args
        ).strip("\n")