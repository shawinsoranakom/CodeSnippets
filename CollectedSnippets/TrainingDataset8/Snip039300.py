def test_cached_st_function_replay_outer_blocks(self, _, cache_decorator):
        @cache_decorator
        def foo(i):
            st.text(i)
            return i

        with st.container():
            foo(1)
            st.text("---")
            foo(1)

        text = self.get_text_delta_contents()
        assert text == ["1", "---", "1"]