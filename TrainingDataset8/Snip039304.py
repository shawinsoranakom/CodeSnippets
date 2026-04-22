def test_cached_st_function_replay_outer_direct(self, _, cache_decorator):
        cont = st.container()

        @cache_decorator
        def foo(i):
            cont.text(i)
            return i

        with self.assertRaises(CacheReplayClosureError):
            foo(1)
            st.text("---")
            foo(1)