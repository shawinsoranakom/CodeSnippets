def test_get_widget_user_key_none(self):
        state = get_script_run_ctx().session_state._state
        st.selectbox("selectbox", options=["foo", "bar"])

        k = list(state._keys())[0]
        # Absence of a user key is represented as None throughout our code
        assert user_key_from_widget_id(k) is None