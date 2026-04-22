def _get_message_from_func(self, orig_exc, cached_func, hash_func):
        args = _get_error_message_args(orig_exc, cached_func)

        if hasattr(hash_func, "__name__"):
            args["hash_func_name"] = "`%s()`" % hash_func.__name__
        else:
            args["hash_func_name"] = "a function"

        return (
            """
%(orig_exception_desc)s

This error is likely due to a bug in %(hash_func_name)s, which is a
user-defined hash function that was passed into the `@st.cache` decorator of
%(object_desc)s.

%(hash_func_name)s failed when hashing an object of type
`%(failed_obj_type_str)s`.  If you don't know where that object is coming from,
try looking at the hash chain below for an object that you do recognize, then
pass that to `hash_funcs` instead:

```
%(hash_stack)s
```

If you think this is actually a Streamlit bug, please [file a bug report here.]
(https://github.com/streamlit/streamlit/issues/new/choose)
            """
            % args
        ).strip("\n")