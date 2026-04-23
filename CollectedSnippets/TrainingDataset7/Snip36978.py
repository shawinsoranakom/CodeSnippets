def test_sensitive_variables_not_called(self):
        msg = (
            "sensitive_variables() must be called to use it as a decorator, "
            "e.g., use @sensitive_variables(), not @sensitive_variables."
        )
        with self.assertRaisesMessage(TypeError, msg):

            @sensitive_variables
            def test_func(password):
                pass