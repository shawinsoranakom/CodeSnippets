def test_cached_st_function_replay_nested(self, _, cache_decorator):
        @cache_decorator
        def inner(i):
            st.text(i)

        @cache_decorator
        def outer(i):
            inner(i)
            st.text(i + 10)

        outer(1)
        outer(1)
        st.text("---")
        inner(2)
        outer(2)
        st.text("---")
        outer(3)
        inner(3)

        text = self.get_text_delta_contents()
        assert text == [
            "1",
            "11",
            "1",
            "11",
            "---",
            "2",
            "2",
            "12",
            "---",
            "3",
            "13",
            "3",
        ]