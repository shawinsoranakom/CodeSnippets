def test_cull_nonexistent(self):
        generated_widget_key = f"{GENERATED_WIDGET_KEY_PREFIX}-removed_widget"

        self.session_state._old_state = {
            "existing_widget": True,
            generated_widget_key: True,
            "val_set_via_state": 5,
        }

        wstates = WStates()
        self.session_state._new_widget_state = wstates

        self.session_state._cull_nonexistent({"existing_widget"})

        assert self.session_state["existing_widget"] == True
        assert generated_widget_key not in self.session_state
        assert self.session_state["val_set_via_state"] == 5