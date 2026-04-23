def __init_subclass__(cls, **kwargs: t.Any) -> None:
        import warnings

        # These method signatures were updated to take a ctx param. Detect
        # overridden methods in subclasses that still have the old signature.
        # Show a deprecation warning and wrap to call with correct args.
        for method in (
            cls.handle_http_exception,
            cls.handle_user_exception,
            cls.handle_exception,
            cls.log_exception,
            cls.dispatch_request,
            cls.full_dispatch_request,
            cls.finalize_request,
            cls.make_default_options_response,
            cls.preprocess_request,
            cls.process_response,
            cls.do_teardown_request,
            cls.do_teardown_appcontext,
        ):
            base_method = getattr(Flask, method.__name__)

            if method is base_method:
                # not overridden
                continue

            # get the second parameter (first is self)
            iter_params = iter(inspect.signature(method).parameters.values())
            next(iter_params)
            param = next(iter_params, None)

            # must have second parameter named ctx or annotated AppContext
            if param is None or not (
                # no annotation, match name
                (param.annotation is inspect.Parameter.empty and param.name == "ctx")
                or (
                    # string annotation, access path ends with AppContext
                    isinstance(param.annotation, str)
                    and param.annotation.rpartition(".")[2] == "AppContext"
                )
                or (
                    # class annotation
                    inspect.isclass(param.annotation)
                    and issubclass(param.annotation, AppContext)
                )
            ):
                warnings.warn(
                    f"The '{method.__name__}' method now takes 'ctx: AppContext'"
                    " as the first parameter. The old signature is deprecated"
                    " and will not be supported in Flask 4.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                setattr(cls, method.__name__, remove_ctx(method))
                setattr(Flask, method.__name__, add_ctx(base_method))