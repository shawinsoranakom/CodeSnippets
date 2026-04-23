def template(
        self,
        variable: t.Any,  # DTFIX-FUTURE: once we settle the new/old API boundaries, rename this (here and in other methods)
        *,
        options: TemplateOptions = TemplateOptions.DEFAULT,
        mode: TemplateMode = TemplateMode.DEFAULT,
        lazy_options: LazyOptions = LazyOptions.DEFAULT,
    ) -> t.Any:
        """Templates (possibly recursively) any given data as input."""
        original_variable = variable

        for _attempt in range(TRANSFORM_CHAIN_LIMIT):
            if variable is None or (value_type := type(variable)) in IGNORE_SCALAR_VAR_TYPES:
                return variable  # quickly ignore supported scalar types which are not be templated

            if is_expression := type(variable) is TemplateExpressionWrapper:  # pylint: disable=unidiomatic-typecheck
                variable = variable.expression

            value_is_str = isinstance(variable, str)

            if template_ctx := TemplateContext.current(optional=True):
                stop_on_template = template_ctx.stop_on_template
            else:
                stop_on_template = False

            if mode is TemplateMode.STOP_ON_TEMPLATE:
                stop_on_template = True

            with (
                TemplateContext(template_value=variable, templar=self, options=options, stop_on_template=stop_on_template) as ctx,
                DeprecatedAccessAuditContext.when(ctx.is_top_level),
                JinjaCallContext(accept_lazy_markers=True),  # let default Jinja marker behavior apply, since we're descending into a new template
            ):
                try:
                    if not value_is_str:
                        # transforms are currently limited to non-str types as an optimization
                        if (transform := _type_transform_mapping.get(value_type)) and value_type.__name__ not in lazy_options.unmask_type_names:
                            variable = transform(variable)
                            continue

                        template_result = _AnsibleLazyTemplateMixin._try_create(variable, lazy_options)
                    elif not lazy_options.template:
                        template_result = variable
                    elif not is_expression and not is_possibly_template(variable, options.overrides):
                        template_result = variable
                    elif not self._trust_check(variable, skip_handler=stop_on_template):
                        template_result = variable
                    elif stop_on_template:
                        raise TemplateEncountered()
                    else:
                        compiled_template = self._compile_expression(variable, options) if is_expression else self._compile_template(variable, options)

                        template_result = compiled_template(self.available_variables)
                        template_result = self._post_render_mutation(variable, template_result, options)
                except TemplateEncountered:
                    raise
                except Exception as ex:
                    template_result = defer_template_error(ex, variable, is_expression=is_expression)

                if ctx.is_top_level or mode is TemplateMode.ALWAYS_FINALIZE:
                    template_result = self._finalize_top_level_template_result(
                        variable, options, template_result, stop_on_container=mode is TemplateMode.STOP_ON_CONTAINER
                    )

            return template_result

        raise AnsibleTemplateTransformLimitError(obj=original_variable)