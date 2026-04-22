def __init__(self, func: types.FunctionType, return_value: types.FunctionType):
        MarkdownFormattedException.__init__(
            self,
            f"""
            Cannot serialize the return value (of type {get_return_value_type(return_value)}) in {get_cached_func_name_md(func)}.
            `st.experimental_memo` uses [pickle](https://docs.python.org/3/library/pickle.html) to
            serialize the function’s return value and safely store it in the cache without mutating the original object. Please convert the return value to a pickle-serializable type.
            If you want to cache unserializable objects such as database connections or Tensorflow
            sessions, use `st.experimental_singleton` instead (see [our docs](https://docs.streamlit.io/library/advanced-features/experimental-cache-primitives) for differences).""",
        )