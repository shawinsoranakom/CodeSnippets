def wrapper(*args, **kwargs):
        named_args = {**dict(zip(fn_spec.arg_names, args)), **kwargs}
        assert len(named_args) > 0
        first_arg = next(iter(named_args.values()))
        desugaring_context = (
            first_arg if isinstance(first_arg, DesugaringContext) else None
        )

        this_substitution = {}
        if desugaring_context is not None:
            this_substitution.update(desugaring_context._substitution)

        for key, value in substitution_param.items():
            assert isinstance(value, str)
            this_substitution[key] = named_args[value]

        args = _desugar_this_args(this_substitution, args)
        kwargs = _desugar_this_kwargs(this_substitution, kwargs)

        if desugaring_context is not None:
            args = tuple(
                desugaring_context._desugaring.eval_expression(arg) for arg in args
            )
            kwargs = {
                key: desugaring_context._desugaring.eval_expression(value)
                for key, value in kwargs.items()
            }
        return func(*args, **kwargs)