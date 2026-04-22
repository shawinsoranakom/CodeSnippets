def test_widget_outputs_dont_alias(self):
        color = st.select_slider(
            "Select a color of the rainbow",
            options=[
                ["red", "orange"],
                ["yellow", "green"],
                ["blue", "indigo"],
                ["violet"],
            ],
            key="color",
        )

        ctx = get_script_run_ctx()
        assert ctx.session_state["color"] is not color