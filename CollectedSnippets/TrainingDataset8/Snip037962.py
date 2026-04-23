def _get_message(self, orig_exc: BaseException, failed_obj: Any) -> str:
        args = _get_error_message_args(orig_exc, failed_obj)

        # This needs to have zero indentation otherwise %(hash_stack)s will
        # render incorrectly in Markdown.
        return (
            """
%(orig_exception_desc)s

While caching %(object_part)s %(object_desc)s, Streamlit encountered an
object of type `%(failed_obj_type_str)s`, which it does not know how to hash.

**In this specific case, it's very likely you found a Streamlit bug so please
[file a bug report here.]
(https://github.com/streamlit/streamlit/issues/new/choose)**

In the meantime, you can try bypassing this error by registering a custom
hash function via the `hash_funcs` keyword in @st.cache(). For example:

```
@st.cache(hash_funcs={%(failed_obj_type_str)s: my_hash_func})
def my_func(...):
    ...
```

If you don't know where the object of type `%(failed_obj_type_str)s` is coming
from, try looking at the hash chain below for an object that you do recognize,
then pass that to `hash_funcs` instead:

```
%(hash_stack)s
```

Please see the `hash_funcs` [documentation]
(https://docs.streamlit.io/library/advanced-features/caching#the-hash_funcs-parameter)
for more details.
            """
            % args
        ).strip("\n")