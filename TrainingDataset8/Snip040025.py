def test_get_widget_user_key_hyphens(self):
        state = get_script_run_ctx().session_state._state
        st.slider("slider", key="my-slider")

        k = list(state._keys())[0]
        assert user_key_from_widget_id(k) == "my-slider"