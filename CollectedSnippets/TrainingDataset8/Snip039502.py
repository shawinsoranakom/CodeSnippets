def test_unhashable_type(self):
        @st.cache
        def unhashable_type_func():
            return NotHashable()

        with self.assertRaises(hashing.UnhashableTypeError) as cm:
            unhashable_type_func()

        ep = ExceptionProto()
        exception.marshall(ep, cm.exception)

        self.assertEqual(ep.type, "UnhashableTypeError")

        self.assertTrue(
            normalize_md(ep.message).startswith(
                normalize_md(
                    """
Cannot hash object of type `tests.streamlit.runtime.legacy_caching.caching_test.NotHashable`, found in the return value of
`unhashable_type_func()`.

While caching the return value of `unhashable_type_func()`, Streamlit encountered an
object of type `tests.streamlit.runtime.legacy_caching.caching_test.NotHashable`, which it does not know how to hash.

To address this, please try helping Streamlit understand how to hash that type
by passing the `hash_funcs` argument into `@st.cache`. For example:

```
@st.cache(hash_funcs={tests.streamlit.runtime.legacy_caching.caching_test.NotHashable: my_hash_func})
def my_func(...):
    ...
```

If you don't know where the object of type `tests.streamlit.runtime.legacy_caching.caching_test.NotHashable` is coming
from, try looking at the hash chain below for an object that you do recognize,
then pass that to `hash_funcs` instead:

```
Object of type tests.streamlit.runtime.legacy_caching.caching_test.NotHashable:
                    """
                )
            )
        )

        # Stack trace doesn't show in test :(
        # self.assertNotEqual(len(ep.stack_trace), 0)
        self.assertEqual(ep.message_is_markdown, True)
        self.assertEqual(ep.is_warning, False)