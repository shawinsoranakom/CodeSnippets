def test_get_widget_user_key_incorrect_none(self):
        state = get_script_run_ctx().session_state._state
        st.checkbox("checkbox", key="None")

        k = list(state._keys())[0]
        # Incorrectly inidcates no user key
        assert user_key_from_widget_id(k) == None