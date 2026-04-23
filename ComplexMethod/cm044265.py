async def _execute_func(  # pylint: disable=too-many-positional-arguments
        cls,
        route: str,
        args: tuple[Any, ...],
        execution_context: ExecutionContext,
        func: Callable,
        kwargs: dict[str, Any],
    ) -> OBBject:
        """Execute a function and return the output."""
        user_settings = execution_context.user_settings
        system_settings = execution_context.system_settings
        raised_warnings: list = []
        custom_headers: dict[str, Any] | None = None

        try:
            with catch_warnings(record=True) as warning_list:
                # If we're on Jupyter we need to pop here because we will lose "chart" after
                # ParametersBuilder.build. This needs to be fixed in a way that chart is
                # added to the function signature and shared for jupyter and api
                # We can check in the router decorator if the given function has a chart
                # in the charting extension then we add it there. This way we can remove
                # the chart parameter from the commands.py and package_builder, it will be
                # added to the function signature in the router decorator
                # If the ProviderInterface is not in use, we need to pass a copy of the
                # kwargs dictionary before it is validated, otherwise we lose those items.
                kwargs_copy = deepcopy(kwargs)
                chart = kwargs.pop("chart", False)
                kwargs_copy = deepcopy(kwargs)
                kwargs = ParametersBuilder.build(
                    args=args,
                    execution_context=execution_context,
                    func=func,
                    kwargs=kwargs,
                )
                kwargs = kwargs if kwargs is not None else {}
                # If **kwargs is in the function signature, we need to make sure to pass
                # All kwargs to the function so dependency injection happens
                # and kwargs are actually made available as locals within the function.
                if "kwargs" in kwargs_copy:
                    for k, v in kwargs_copy["kwargs"].items():
                        if k not in kwargs:
                            kwargs[k] = v
                # If we're on the api we need to remove "chart" here because the parameter is added on
                # commands.py and the function signature does not expect "chart"
                kwargs.pop("chart", None)
                # We also pop custom headers
                model_headers = system_settings.api_settings.custom_headers or {}
                custom_headers = {
                    name: kwargs.pop(name.replace("-", "_"), default)
                    for name, default in model_headers.items() or {}
                } or None

                obbject = await cls._command(func, kwargs)
                # The output might be from a router command with 'no_validate=True'
                # It might be of a different type than OBBject.
                # In this case, we avoid accessing those attributes.
                if isinstance(obbject, OBBject):
                    # This section prepares the obbject to pass to the charting service.
                    obbject._route = route  # pylint: disable=protected-access
                    std_params = cls._extract_params(kwargs, "standard_params") or (
                        kwargs if "data" in kwargs else {}
                    )
                    extra_params = cls._extract_params(kwargs, "extra_params") or kwargs
                    obbject._standard_params = (  # pylint: disable=protected-access
                        std_params
                    )
                    obbject._extra_params = (  # pylint: disable=protected-access
                        extra_params
                    )
                    if chart and obbject.results:
                        if "extra_params" not in kwargs_copy:
                            kwargs_copy["extra_params"] = {}
                        # Restore any kwargs passed that were removed by the ParametersBuilder
                        for k in kwargs_copy.copy():
                            if k == "chart":
                                kwargs_copy.pop("chart", None)
                                continue
                            if (
                                not extra_params or k not in extra_params
                            ) and k != "extra_params":
                                kwargs_copy["extra_params"][k] = kwargs_copy.pop(
                                    k, None
                                )

                        cls._chart(obbject, **kwargs_copy)

                raised_warnings = warning_list if warning_list else []
        finally:
            if raised_warnings:
                if isinstance(obbject, OBBject):
                    obbject.warnings = []
                for w in raised_warnings:
                    if isinstance(obbject, OBBject):
                        obbject.warnings.append(cast_warning(w))  # type: ignore
                    if user_settings.preferences.show_warnings:
                        showwarning(
                            message=w.message,
                            category=w.category,
                            filename=w.filename,
                            lineno=w.lineno,
                            file=w.file,
                            line=w.line,
                        )

            if system_settings.logging_suppress is False:
                # pylint: disable=import-outside-toplevel
                from openbb_core.app.logs.logging_service import LoggingService

                ls = LoggingService(system_settings, user_settings)
                ls.log(
                    user_settings=user_settings,
                    system_settings=system_settings,
                    route=route,
                    func=func,
                    kwargs=kwargs,
                    exec_info=exc_info(),
                    custom_headers=custom_headers,
                )

        return obbject