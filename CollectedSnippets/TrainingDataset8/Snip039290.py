def tearDown(self):
        # Clear caches
        st.experimental_memo.clear()
        st.experimental_singleton.clear()

        # And some tests create widgets, and can result in DuplicateWidgetID
        # errors on subsequent runs.
        ctx = script_run_context.get_script_run_ctx()
        if ctx is not None:
            ctx.widget_ids_this_run.clear()
            ctx.widget_user_keys_this_run.clear()

        super().tearDown()