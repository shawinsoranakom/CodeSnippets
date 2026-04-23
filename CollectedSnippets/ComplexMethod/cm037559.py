def __init__(
        self,
        op: IrOp,
        provider: str,
        impl_fn: Callable,
        supported: bool,
        supports_args: Callable[..., bool] | None,
    ):
        assert provider not in op.impls, (
            f"Implementation for provider {provider} already registered."
        )
        # Native also uses this path, so we allow it here.
        assert provider == "native" or provider not in RESERVED_PROVIDERS

        # Enforce the exact same schema as the native implementation.
        # This takes care of names, types, and defaults.
        schema = infer_schema(impl_fn, mutates_args=[])
        if schema != op._schema_str:
            raise ValueError(
                f"Implementation for provider {provider} has schema '{schema}' which "
                f"does not match native schema '{op._schema_str}' for op {op.name}."
            )

        if supports_args is not None:
            if not callable(supports_args):
                raise ValueError(
                    f"supports_args for provider {provider} must be a callable"
                )

            # We also manually validate the supports_args signature.
            # Matching signatures allow faster dispatch on the hotpath.

            # Check that supports_args does not have keyword-only parameters
            supports_args_signature = inspect.signature(supports_args)
            params = supports_args_signature.parameters
            if any(p.kind == inspect.Parameter.KEYWORD_ONLY for p in params.values()):
                raise ValueError(
                    f"supports_args for provider {provider} "
                    f"cannot have keyword-only parameters"
                )

            # Check that supports_args has the same total number of parameters
            op_params = op._py_signature.parameters
            if len(params) != len(op_params):
                raise ValueError(
                    f"supports_args for provider {provider} must have the same number "
                    f"of parameters ({len(params)}) as the native implementation "
                    f"({len(op_params)})"
                )

            # Check that names and defaults match for supports_args
            for p, op_p in zip(params.values(), op_params.values()):
                if p.name != op_p.name:
                    raise ValueError(
                        f"supports_args for provider {provider} has parameter "
                        f"'{p.name}' which does not match native parameter "
                        f"'{op_p.name}'"
                    )
                if p.default != op_p.default:
                    raise ValueError(
                        f"supports_args for provider {provider} has parameter "
                        f"'{p.name}' with default {p.default} which does not match "
                        f"native default {op_p.default}'"
                    )

        self.op = op
        self.provider = provider
        self.impl_fn = impl_fn
        self.supported = supported
        self._supports_args = supports_args