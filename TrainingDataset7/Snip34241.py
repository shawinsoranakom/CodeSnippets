def test_simple_tag_registration(self):
        # The decorators preserve the decorated function's docstring, name,
        # and attributes.
        self.verify_tag(custom.no_params, "no_params")
        self.verify_tag(custom.one_param, "one_param")
        self.verify_tag(custom.explicit_no_context, "explicit_no_context")
        self.verify_tag(custom.no_params_with_context, "no_params_with_context")
        self.verify_tag(custom.params_and_context, "params_and_context")
        self.verify_tag(
            custom.simple_unlimited_args_kwargs, "simple_unlimited_args_kwargs"
        )