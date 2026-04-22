def __init__(
        self,
        cache_type: CacheType,
        cached_func: types.FunctionType,
    ):
        func_name = get_cached_func_name_md(cached_func)
        decorator_name = (cache_type.value,)

        msg = (
            f"""
While running {func_name}, a streamlit element is called on some layout block created outside the function.
This is incompatible with replaying the cached effect of that element, because the
the referenced block might not exist when the replay happens.

How to fix this:
* Move the creation of $THING inside {func_name}.
* Move the call to the streamlit element outside of {func_name}.
* Remove the `@st.{decorator_name}` decorator from {func_name}.
            """
        ).strip("\n")

        super().__init__(msg)