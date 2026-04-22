def test_cached_st_function_replay_inner_direct(self, _, cache_decorator):
        @cache_decorator(show_spinner=False)
        def foo(i):
            cont = st.container()
            cont.text(i)
            return i

        foo(1)  # [0,0] and [0,0,0]
        st.text("---")  # [0,1]
        foo(1)  # [0,2] and [0,2,0]

        text = self.get_text_delta_contents()
        assert text == ["1", "---", "1"]

        paths = [
            msg.metadata.delta_path
            for msg in self.forward_msg_queue._queue
            if msg.HasField("delta")
        ]
        assert paths == [[0, 0], [0, 0, 0], [0, 1], [0, 2], [0, 2, 0]]