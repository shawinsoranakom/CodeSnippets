def _post_validate_args(self, attr: str, value: t.Any, templar: TemplateEngine) -> dict[str, t.Any]:
        try:
            self.action = templar.template(self.action)
        except AnsibleValueOmittedError:
            # some strategies may trigger this error when templating task.action, but backstop here if not
            raise AnsibleParserError("Omit is not valid for the `action` keyword.", obj=self.action) from None

        action_context = action_loader.get_with_context(self.action, collection_list=self.collections, class_only=True)

        if not action_context.plugin_load_context.resolved:
            module_or_action_context = module_loader.find_plugin_with_context(self.action, collection_list=self.collections)

            if not module_or_action_context.resolved:
                raise AnsibleError(f"Cannot resolve {self.action!r} to an action or module.", obj=self.action)

            action_context = action_loader.get_with_context('ansible.legacy.normal', collection_list=self.collections, class_only=True)
        else:
            module_or_action_context = action_context.plugin_load_context

        self._resolved_action = module_or_action_context.resolved_fqcn

        action_type: type[ActionBase] = action_context.object

        vp = value.pop('_variable_params', None)

        supports_raw_params = action_type.supports_raw_params or module_or_action_context.resolved_fqcn in RAW_PARAM_MODULES

        if supports_raw_params:
            raw_params_to_finalize = None
        else:
            raw_params_to_finalize = value.pop('_raw_params', None)  # always str or None

            # TaskArgsFinalizer performs more thorough type checking, but this provides a friendlier error message for a subset of detected cases.
            if raw_params_to_finalize and not is_possibly_all_template(raw_params_to_finalize):
                raise AnsibleError(f'Action {module_or_action_context.resolved_fqcn!r} does not support raw params.', obj=self.action)

        args_finalizer = _task.TaskArgsFinalizer(
            _get_action_arg_defaults(module_or_action_context.resolved_fqcn, self, templar),
            vp,
            raw_params_to_finalize,
            value,
            templar=templar,
        )

        try:
            with action_type.get_finalize_task_args_context() as finalize_context:
                args = args_finalizer.finalize(action_type.finalize_task_arg, context=finalize_context)
        except Exception as ex:
            raise AnsibleError(f'Finalization of task args for {module_or_action_context.resolved_fqcn!r} failed.', obj=self.action) from ex

        if self._origin:
            args = self._origin.tag(args)

        return args