def test_user_hash_error(self):
        class MyObj(object):
            pass

        def bad_hash_func(x):
            x += 10  # Throws a TypeError since x has type MyObj.
            return x

        @st.cache(hash_funcs={MyObj: bad_hash_func})
        def user_hash_error_func(x):
            pass

        with self.assertRaises(hashing.UserHashError) as cm:
            my_obj = MyObj()
            user_hash_error_func(my_obj)

        ep = ExceptionProto()
        exception.marshall(ep, cm.exception)

        self.assertEqual(ep.type, "TypeError")
        self.assertTrue(
            normalize_md(ep.message).startswith(
                normalize_md(
                    """
unsupported operand type(s) for +=: 'MyObj' and 'int'

This error is likely due to a bug in `bad_hash_func()`, which is a user-defined
hash function that was passed into the `@st.cache` decorator of `user_hash_error_func()`.

`bad_hash_func()` failed when hashing an object of type
`tests.streamlit.runtime.legacy_caching.caching_test.CacheErrorsTest.test_user_hash_error.<locals>.MyObj`.  If you
don't know where that object is coming from, try looking at the hash chain below
for an object that you do recognize, then pass that to `hash_funcs` instead:

```
Object of type tests.streamlit.runtime.legacy_caching.caching_test.CacheErrorsTest.test_user_hash_error.<locals>.MyObj:
<tests.streamlit.runtime.legacy_caching.caching_test.CacheErrorsTest.test_user_hash_error.<locals>.MyObj object at
                    """
                )
            )
        )

        # Stack trace doesn't show in test :(
        # self.assertNotEqual(len(ep.stack_trace), 0)
        self.assertEqual(ep.message_is_markdown, True)
        self.assertEqual(ep.is_warning, False)