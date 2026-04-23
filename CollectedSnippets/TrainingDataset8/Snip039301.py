def test_cached_st_function_replay_sidebar(self, _, cache_decorator):
        @cache_decorator(show_spinner=False)
        def foo(i):
            st.sidebar.text(i)
            return i

        foo(1)  # [1,0]
        st.text("---")  # [0,0]
        foo(1)  # [1,1]

        text = [
            get_text_or_block(delta)
            for delta in self.get_all_deltas_from_queue()
            if get_text_or_block(delta) is not None
        ]
        assert text == ["1", "---", "1"]

        paths = [
            msg.metadata.delta_path
            for msg in self.forward_msg_queue._queue
            if msg.HasField("delta")
        ]
        assert paths == [[1, 0], [0, 0], [1, 1]]