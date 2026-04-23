def __init__(self, config_option, msg, *args):
        message = """
{0}

You can disable this warning by disabling the config option:
`{1}`

```
st.set_option('{1}', False)
```
or in your `.streamlit/config.toml`
```
[deprecation]
{2} = false
```
    """.format(
            msg, config_option, config_option.split(".")[1]
        )
        # TODO: create a deprecation docs page to add to deprecation msg #1669
        # For more details, please see: https://docs.streamlit.io/path/to/deprecation/docs.html

        super().__init__(message, *args)