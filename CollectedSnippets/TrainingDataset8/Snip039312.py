def tearDown(self):
        # Some of these tests reach directly into CALL_STACK data and twiddle it.
        # Reset default values on teardown.
        MEMO_CALL_STACK._cached_func_stack = []
        MEMO_CALL_STACK._suppress_st_function_warning = 0
        SINGLETON_CALL_STACK._cached_func_stack = []
        SINGLETON_CALL_STACK._suppress_st_function_warning = 0

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