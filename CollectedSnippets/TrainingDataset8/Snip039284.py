def test_unhashable_type(self):
        @st.experimental_memo
        def unhashable_type_func(lock: threading.Lock):
            return str(lock)

        with self.assertRaises(UnhashableParamError) as cm:
            unhashable_type_func(threading.Lock())

        ep = ExceptionProto()
        exception.marshall(ep, cm.exception)

        self.assertEqual(ep.type, "UnhashableParamError")

        expected_message = """
Cannot hash argument 'lock' (of type `_thread.lock`) in 'unhashable_type_func'.

To address this, you can tell Streamlit not to hash this argument by adding a
leading underscore to the argument's name in the function signature:

```
@st.experimental_memo
def unhashable_type_func(_lock, ...):
    ...
```
                    """

        self.assertEqual(
            testutil.normalize_md(expected_message), testutil.normalize_md(ep.message)
        )
        # Stack trace doesn't show in test :(
        # self.assertNotEqual(len(ep.stack_trace), 0)
        self.assertEqual(ep.message_is_markdown, True)
        self.assertEqual(ep.is_warning, False)