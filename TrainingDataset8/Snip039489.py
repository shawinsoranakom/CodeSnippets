def test_mutate_args(self, exception):
        @st.cache
        def foo(d):
            d["answer"] += 1
            return d["answer"]

        d = {"answer": 0}

        self.assertNotEqual(foo(d), foo(d))

        exception.assert_not_called()