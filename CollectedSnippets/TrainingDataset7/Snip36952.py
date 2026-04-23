def test_sensitive_function_arguments(self):
        """
        Sensitive variables don't leak in the sensitive_variables decorator's
        frame, when those variables are passed as arguments to the decorated
        function.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(sensitive_args_function_caller)
            self.verify_unsafe_email(sensitive_args_function_caller)

        with self.settings(DEBUG=False):
            self.verify_safe_response(
                sensitive_args_function_caller, check_for_POST_params=False
            )
            self.verify_safe_email(
                sensitive_args_function_caller, check_for_POST_params=False
            )