def test_get_widget_user_key(self):
        state = get_script_run_ctx().session_state._state
        st.checkbox("checkbox", key="c")

        k = list(state._keys())[0]
        assert user_key_from_widget_id(k) == "c"