def test_cached_st_function_replay(self, _, cache_decorator):
        @cache_decorator
        def foo_replay(i):
            st.text(i)
            return i

        foo_replay(1)
        st.text("---")
        foo_replay(1)

        text = self.get_text_delta_contents()

        assert text == ["1", "---", "1"]