def get_example_value(
        self,
        base_cls_vt: VariableTracker,
        cls_vt: VariableTracker,
        init_args: list[VariableTracker],
    ) -> Any:
        user_cls = cls_vt.value  # type: ignore[attr-defined]
        if issubclass(user_cls, torch.nn.Module):
            # TODO(anijain2305) - Is it possible to remove this specialization?
            obj = nn_module_new(user_cls)
        else:
            if isinstance(base_cls_vt, variables.BuiltinVariable):
                base_cls = base_cls_vt.fn
            elif isinstance(base_cls_vt, variables.DictBuiltinVariable):
                base_cls = dict
            elif isinstance(base_cls_vt, variables.ListBuiltinVariable):
                base_cls = list
            elif isinstance(base_cls_vt, variables.UserDefinedClassVariable):
                base_cls = base_cls_vt.value
            else:
                raise RuntimeError(f"Unexpected base_cls_vt {base_cls_vt}")

            assert variables.UserDefinedClassVariable.is_supported_new_method(
                base_cls.__new__
            )
            if is_structseq_class(user_cls):
                # Structseq tp_new requires a sequence argument and rejects
                # tuple.__new__, so create a dummy with None placeholders.
                obj = user_cls([None] * user_cls.n_fields)
            elif init_args and issubclass(
                user_cls,
                variables.user_defined._CONSTANT_BASE_TYPES,
            ):
                example_args = [arg.as_python_constant() for arg in init_args]
                try:
                    obj = base_cls.__new__(  # pyrefly: ignore[bad-specialization]
                        user_cls, *example_args
                    )
                except Exception:
                    # __new__ can raise (e.g., exceeding int str digit limits).
                    # Fall back to creating without args — the example value is
                    # only used for tracing, not for correctness.
                    obj = base_cls.__new__(  # pyrefly: ignore[bad-specialization]
                        user_cls
                    )
            else:
                obj = base_cls.__new__(user_cls)
        return obj