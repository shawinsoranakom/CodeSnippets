def test_inclusion_tag_registration(self):
        # The decorators preserve the decorated function's docstring, name,
        # and attributes.
        self.verify_tag(inclusion.inclusion_no_params, "inclusion_no_params")
        self.verify_tag(inclusion.inclusion_one_param, "inclusion_one_param")
        self.verify_tag(
            inclusion.inclusion_explicit_no_context, "inclusion_explicit_no_context"
        )
        self.verify_tag(
            inclusion.inclusion_no_params_with_context,
            "inclusion_no_params_with_context",
        )
        self.verify_tag(
            inclusion.inclusion_params_and_context, "inclusion_params_and_context"
        )
        self.verify_tag(inclusion.inclusion_two_params, "inclusion_two_params")
        self.verify_tag(inclusion.inclusion_one_default, "inclusion_one_default")
        self.verify_tag(inclusion.inclusion_unlimited_args, "inclusion_unlimited_args")
        self.verify_tag(
            inclusion.inclusion_only_unlimited_args, "inclusion_only_unlimited_args"
        )
        self.verify_tag(inclusion.inclusion_tag_use_l10n, "inclusion_tag_use_l10n")
        self.verify_tag(
            inclusion.inclusion_unlimited_args_kwargs, "inclusion_unlimited_args_kwargs"
        )