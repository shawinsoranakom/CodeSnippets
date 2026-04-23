def test_docstring(self):
        """ Verify that the function signature and its docstring match. """
        registry = Registry(get_db_name())
        seen_methods = set()

        for model_name, model_cls in registry.items():
            for method_name, _ in inspect.getmembers(model_cls, inspect.isroutine):
                if method_name.startswith('__'):
                    continue
                if method_name in seen_methods:
                    continue
                seen_methods.add(method_name)

                # We don't care of the docstring in overrides, find the
                # class that introduced the method.
                reverse_mro = reversed(model_cls.mro()[1:-1])
                for parent_class in reverse_mro:
                    method = getattr(parent_class, method_name, None)
                    if callable(method):
                        break
                if not method.__doc__:
                    continue

                if (parent_class._name or '').startswith('mail.'):
                    # don't lint the mail mixins (until we lint them)
                    settings = self.doctree_settings_silent
                elif (model_cls._original_module or model_name).startswith(MODULES_TO_LINT):
                    # lint all methods
                    settings = self.doctree_settings_verbose
                elif (
                    (model_cls._original_module or model_name).startswith(MODULES_TO_LINT_ONLY_PUBLIC_METHODS)
                    and not method_name.startswith('_')
                ):
                    # lint only public methods
                    settings = self.doctree_settings_verbose
                else:
                    # don't lint anything
                    settings = self.doctree_settings_silent

                with self.subTest(
                    module=parent_class._module,
                    model=parent_class._name,
                    method=method_name,
                ):
                    with contextlib.redirect_stderr(io.StringIO()) as stderr:
                        doctree = docutils.core.publish_doctree(
                            inspect.cleandoc(method.__doc__),
                            settings=settings,
                        )
                        if stderr.tell():
                            self.fail(PARSE_ERROR.format(
                                doc=inspect.cleandoc(method.__doc__).strip(),
                                error=stderr.getvalue(),
                            ))

                    self._test_docstring_params(method, doctree)