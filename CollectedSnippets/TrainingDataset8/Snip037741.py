def _create_message(
        cache_type: CacheType,
        func: types.FunctionType,
        arg_name: Optional[str],
        arg_value: Any,
    ) -> str:
        arg_name_str = arg_name if arg_name is not None else "(unnamed)"
        arg_type = type_util.get_fqn_type(arg_value)
        func_name = func.__name__
        arg_replacement_name = f"_{arg_name}" if arg_name is not None else "_arg"

        return (
            f"""
Cannot hash argument '{arg_name_str}' (of type `{arg_type}`) in '{func_name}'.

To address this, you can tell Streamlit not to hash this argument by adding a
leading underscore to the argument's name in the function signature:

```
@st.{cache_type.value}
def {func_name}({arg_replacement_name}, ...):
    ...
```
            """
        ).strip("\n")