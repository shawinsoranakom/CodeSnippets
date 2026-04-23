def __init__(
        self,
        environment: TemplateEnvironment,
        *,
        functions: list[TemplateFunction] | None = None,
    ) -> None:
        """Initialize the extension with a list of template functions."""
        super().__init__(environment)

        if functions:
            for template_func in functions:
                # Skip functions that require hass when hass is not available
                if template_func.requires_hass and self.environment.hass is None:
                    continue

                # Register unsupported stub for functions not allowed in limited environments
                if self.environment.limited and not template_func.limited_ok:
                    unsupported_func = self._create_unsupported_function(
                        template_func.name
                    )
                    if template_func.as_global:
                        environment.globals[template_func.name] = unsupported_func
                    if template_func.as_filter:
                        environment.filters[template_func.name] = unsupported_func
                    if template_func.as_test:
                        environment.tests[template_func.name] = unsupported_func
                    continue

                func = template_func.func

                if template_func.requires_hass:
                    # We wrap these as a context functions to ensure they get
                    # evaluated fresh with every execution, rather than executed
                    # at compile time and the value stored.
                    func = _pass_context(func)

                if template_func.as_global:
                    environment.globals[template_func.name] = func
                if template_func.as_filter:
                    environment.filters[template_func.name] = func
                if template_func.as_test:
                    environment.tests[template_func.name] = func