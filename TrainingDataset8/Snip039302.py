def test_cached_st_function_replay_inner_blocks(self, _, cache_decorator):
        @cache_decorator(show_spinner=False)
        def foo(i):
            with st.container():
                st.text(i)
                return i

        with st.container():  # [0,0]
            st.text(0)  # [0,0,0]
        st.text("---")  # [0,1]
        with st.container():  # [0,2]
            st.text(0)  # [0,2,0]

        foo(1)  # [0,3] and [0,3,0]
        st.text("---")  # [0,4]
        foo(1)  # [0,5] and [0,5,0]

        paths = [
            msg.metadata.delta_path
            for msg in self.forward_msg_queue._queue
            if msg.HasField("delta")
        ]
        assert paths == [
            [0, 0],
            [0, 0, 0],
            [0, 1],
            [0, 2],
            [0, 2, 0],
            [0, 3],
            [0, 3, 0],
            [0, 4],
            [0, 5],
            [0, 5, 0],
        ]