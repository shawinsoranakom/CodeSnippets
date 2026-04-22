def test_st_exception(self, show_error_details: bool):
        """Test st.exception."""
        # client.showErrorDetails has no effect on code that calls
        # st.exception directly. This test should have the same result
        # regardless fo the config option.
        with testutil.patch_config_options(
            {"client.showErrorDetails": show_error_details}
        ):
            e = RuntimeError("Test Exception")
            st.exception(e)

            el = self.get_delta_from_queue().new_element
            self.assertEqual(el.exception.type, "RuntimeError")
            self.assertEqual(el.exception.message, "Test Exception")
            # We will test stack_trace when testing
            # streamlit.elements.exception_element
            self.assertEqual(el.exception.stack_trace, [])