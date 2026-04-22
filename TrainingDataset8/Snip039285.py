def test_unserializable_return_value_error(self):
        @st.experimental_memo
        def unserializable_return_value_func():
            return threading.Lock()

        with self.assertRaises(UnserializableReturnValueError) as cm:
            unserializable_return_value_func()

        ep = ExceptionProto()
        exception.marshall(ep, cm.exception)

        self.assertEqual(ep.type, "UnserializableReturnValueError")

        expected_message = f"""
            Cannot serialize the return value (of type {get_return_value_type(return_value=threading.Lock())}) in `unserializable_return_value_func()`.
            `st.experimental_memo` uses [pickle](https://docs.python.org/3/library/pickle.html) to
            serialize the function’s return value and safely store it in the cache without mutating the original object. Please convert the return value to a pickle-serializable type.
            If you want to cache unserializable objects such as database connections or Tensorflow
            sessions, use `st.experimental_singleton` instead (see [our docs](https://docs.streamlit.io/library/advanced-features/experimental-cache-primitives) for differences)."""

        self.assertEqual(
            testutil.normalize_md(expected_message), testutil.normalize_md(ep.message)
        )
        self.assertEqual(ep.message_is_markdown, True)
        self.assertEqual(ep.is_warning, False)