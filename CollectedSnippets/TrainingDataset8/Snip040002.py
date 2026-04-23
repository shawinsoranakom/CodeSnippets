def test_session_state_stats(self):
        # TODO: document the values used here. They're somewhat arbitrary -
        #  we don't care about actual byte values, but rather that our
        #  SessionState isn't getting unexpectedly massive.
        state = _raw_session_state()
        stat = state.get_stats()[0]
        assert stat.category_name == "st_session_state"

        init_size = stat.byte_length
        assert init_size < 2500

        state["foo"] = 2
        new_size = state.get_stats()[0].byte_length
        assert new_size > init_size
        assert new_size < 2500

        state["foo"] = 1
        new_size_2 = state.get_stats()[0].byte_length
        assert new_size_2 == new_size

        st.checkbox("checkbox", key="checkbox")
        new_size_3 = state.get_stats()[0].byte_length
        assert new_size_3 > new_size_2
        assert new_size_3 - new_size_2 < 2500

        state._compact_state()
        new_size_4 = state.get_stats()[0].byte_length
        assert new_size_4 <= new_size_3