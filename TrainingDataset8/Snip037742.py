def __init__(
        self,
        cache_type: CacheType,
        st_func_name: str,
        cached_func: types.FunctionType,
    ):
        args = {
            "st_func_name": f"`st.{st_func_name}()`",
            "func_name": self._get_cached_func_name_md(cached_func),
            "decorator_name": cache_type.value,
        }

        msg = (
            """
Your script uses %(st_func_name)s to write to your Streamlit app from within
some cached code at %(func_name)s. This code will only be called when we detect
a cache "miss", which can lead to unexpected results.

How to fix this:
* Move the %(st_func_name)s call outside %(func_name)s.
* Or, if you know what you're doing, use `@st.%(decorator_name)s(suppress_st_warning=True)`
to suppress the warning.
            """
            % args
        ).strip("\n")

        super().__init__(msg)