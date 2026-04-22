def test_setting_before_widget_creation(self):
        state = st.session_state
        state.c = True
        assert state.c == True

        c = st.checkbox("checkbox", key="c")
        assert c == True