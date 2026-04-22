def test_cached_st_function_warning(self, _, cache_decorator, call_stack):
        """Ensure we properly warn when interactive st.foo functions are called
        inside a cached function.
        """
        forward_msg_queue = ForwardMsgQueue()
        orig_report_ctx = get_script_run_ctx()
        add_script_run_ctx(
            threading.current_thread(),
            ScriptRunContext(
                session_id="test session id",
                _enqueue=forward_msg_queue.enqueue,
                query_string="",
                session_state=SafeSessionState(SessionState()),
                uploaded_file_mgr=UploadedFileManager(),
                page_script_hash="",
                user_info={"email": "test@test.com"},
            ),
        )
        with patch.object(call_stack, "_show_cached_st_function_warning") as warning:
            st.text("foo")
            warning.assert_not_called()

            @cache_decorator
            def cached_func():
                st.text("Inside cached func")

            cached_func()
            warning.assert_not_called()

            warning.reset_mock()

            # Make sure everything got reset properly
            st.text("foo")
            warning.assert_not_called()

            # Test warning suppression
            @cache_decorator(suppress_st_warning=True)
            def suppressed_cached_func():
                st.text("No warnings here!")

            suppressed_cached_func()

            warning.assert_not_called()

            # Test nested st.cache functions
            @cache_decorator
            def outer():
                @cache_decorator
                def inner():
                    st.text("Inside nested cached func")

                return inner()

            outer()
            warning.assert_not_called()

            warning.reset_mock()

            # Test st.cache functions that raise errors
            with self.assertRaises(RuntimeError):

                @cache_decorator
                def cached_raise_error():
                    st.text("About to throw")
                    raise RuntimeError("avast!")

                cached_raise_error()

            warning.assert_not_called()
            warning.reset_mock()

            # Make sure everything got reset properly
            st.text("foo")
            warning.assert_not_called()

            # Test st.cache functions with widgets
            @cache_decorator
            def cached_widget():
                st.button("Press me!")

            cached_widget()

            warning.assert_called()
            warning.reset_mock()

            # Make sure everything got reset properly
            st.text("foo")
            warning.assert_not_called()

            # Test st.cache functions with widgets enabled
            @cache_decorator(experimental_allow_widgets=True)
            def cached_widget_enabled():
                st.button("Press me too!")

            cached_widget_enabled()

            warning.assert_not_called()
            warning.reset_mock()

            # Make sure everything got reset properly
            st.text("foo")
            warning.assert_not_called()

            add_script_run_ctx(threading.current_thread(), orig_report_ctx)