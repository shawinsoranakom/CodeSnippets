def test_widget_presence(self):
        state = st.session_state

        assert "foo" not in state

        state.foo = "foo"

        assert "foo" in state
        assert state.foo == "foo"