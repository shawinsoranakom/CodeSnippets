def complete(
        cls, func: Callable[P, OBBject], model: str
    ) -> Callable[P, OBBject] | None:
        """Complete function signature."""
        if isclass(return_type := func.__annotations__["return"]) and not issubclass(
            return_type, OBBject
        ):
            return func

        provider_interface = ProviderInterface()

        if model:
            if model not in provider_interface.models:
                if Env().DEBUG_MODE:
                    warnings.warn(
                        message=f"\nSkipping api route '/{func.__name__}'.\n"
                        f"Model '{model}' not found.\n\n"
                        "Check available models in ProviderInterface().models",
                        category=OpenBBWarning,
                    )
                return None
            cls.validate_signature(
                func,
                {
                    "provider_choices": ProviderChoices,
                    "standard_params": StandardParams,
                    "extra_params": ExtraParams,
                },
            )

            func = cls.inject_dependency(
                func=func,
                arg="provider_choices",
                callable_=provider_interface.model_providers[model],
            )

            func = cls.inject_dependency(
                func=func,
                arg="standard_params",
                callable_=provider_interface.params[model]["standard"],
            )

            func = cls.inject_dependency(
                func=func,
                arg="extra_params",
                callable_=provider_interface.params[model]["extra"],
            )

            func = cls.inject_return_annotation(
                func=func,
                annotation=provider_interface.return_annotations[model],
            )

        else:
            func = cls.polish_return_schema(func)
            if (
                "provider_choices" in func.__annotations__
                and func.__annotations__["provider_choices"] == ProviderChoices
            ):
                func = cls.inject_dependency(
                    func=func,
                    arg="provider_choices",
                    callable_=provider_interface.provider_choices,
                )

        return func