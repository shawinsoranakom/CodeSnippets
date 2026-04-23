def test_lint_override_signature(self):
        self.failureException = TypeError
        registry = Registry(get_db_name())

        for model_name, model_cls in registry.items():
            if model_cls._module in MODULES_TO_IGNORE:
                continue
            for method_name, _ in inspect.getmembers(model_cls, inspect.isroutine):
                if (
                    method_name.startswith('__')
                    or method_name in METHODS_TO_IGNORE
                    or (model_name, method_name) in MODEL_METHODS_TO_IGNORE
                ):
                    continue

                # Find the original function definition
                reverse_mro = reversed(model_cls.mro()[1:-1])
                for parent_class in reverse_mro:
                    method = getattr(parent_class, method_name, None)
                    if callable(method):
                        break

                parent_module = get_odoo_module_name(parent_class.__module__)
                original_signature = inspect.signature(method)
                original_decorators = get_decorators(method)
                is_private = method_name.startswith('_')

                # Assert that all child classes correctly override the method
                for child_class in reverse_mro:
                    if method_name not in child_class.__dict__:
                        continue
                    override = getattr(child_class, method_name)

                    child_module = get_odoo_module_name(child_class.__module__)
                    override_signature = inspect.signature(override)
                    override_decorators = get_decorators(override)

                    with self.subTest(module=child_module, model=model_name, method=method_name):
                        try:
                            assert_valid_override(original_signature, override_signature, is_private=is_private)
                            assert override_decorators == original_decorators, "decorators does not match"
                            assert_attribute_override(method, override, is_private=is_private)
                            counter[method_name].hit += 1
                        except AssertionError as exc:
                            counter[method_name].miss += 1
                            msg = failure_message.format(
                                message=exc.args[0],
                                model=model_name,
                                method=method_name,
                                child_module=child_module,
                                parent_module=parent_module,
                                original_signature=original_signature,
                                override_signature=override_signature,
                                original_decorators=original_decorators,
                                override_decorators=override_decorators,
                            )
                            raise TypeError(msg) from None