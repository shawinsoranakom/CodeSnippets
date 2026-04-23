async def run(
        cls,
        execution_context: ExecutionContext,
        /,
        *args,
        **kwargs,
    ) -> OBBject:
        """Run a command and return the OBBject as output."""
        timestamp = datetime.now()
        start_ns = perf_counter_ns()

        command_map = execution_context.command_map
        route = execution_context.route

        if func := command_map.get_command(route=route):
            obbject = await cls._execute_func(
                route=route,
                args=args,  # type: ignore
                execution_context=execution_context,
                func=func,
                kwargs=kwargs,
            )
        else:
            raise AttributeError(f"Invalid command : route={route}")

        duration = perf_counter_ns() - start_ns

        if execution_context.user_settings.preferences.metadata and isinstance(
            obbject, OBBject
        ):
            try:
                obbject.extra["metadata"] = Metadata(
                    arguments=kwargs,
                    duration=duration,
                    route=route,
                    timestamp=timestamp,
                )
            except Exception as e:
                if Env().DEBUG_MODE:
                    raise OpenBBError(e) from e
                warn(str(e), OpenBBWarning)

            # Remove the dependency injection objects embedded in the kwargs
            deps = execution_context.api_route.dependencies
            dependency_param_names: set[str] = set()
            if deps:
                for dep in deps:
                    dep_name = getattr(dep.dependency, "__name__", "")
                    dep_name = to_snake_case(dep_name).replace("get_", "")
                    dependency_param_names.add(dep_name)

                for dep_key in dependency_param_names:
                    _ = obbject._extra_params.pop(  # type:ignore  # pylint: disable=W0212
                        dep_key, None
                    )

            meta = getattr(obbject.extra.get("metadata"), "arguments", {})

            # Non-provider endpoints need to have execution info added because it might have been discarded.
            if meta and (
                not meta.get("provider_choices", {})
                and not meta.get("standard_params", {})
                and not meta.get("extra_params", {})
            ):
                for k, v in kwargs.items():
                    if k == "kwargs":
                        for key, value in kwargs["kwargs"].items():
                            if key not in dependency_param_names and value:
                                obbject.extra["metadata"].arguments["extra_params"][
                                    key
                                ] = value
                        continue
                    if k not in dependency_param_names and v:
                        obbject.extra["metadata"].arguments["standard_params"][k] = v

        if isinstance(obbject, OBBject):
            try:
                cls._trigger_command_output_callbacks(route, obbject)
            except Exception as e:
                if Env().DEBUG_MODE:
                    raise OpenBBError(e) from e
                warn(str(e), OpenBBWarning)
            # We need to remove callables that were added to
            # kwargs representing dependency injections
            metadata = obbject.extra.get("metadata")
            if metadata:
                arguments = obbject.extra["metadata"].arguments

                for section in ("standard_params", "extra_params", "provider_choices"):
                    params = arguments.get(section)

                    if not isinstance(params, dict):
                        continue

                    for key, value in params.copy().items():
                        if callable(value) or not value:
                            del obbject.extra["metadata"].arguments[section][key]
                            continue
                        try:
                            jsonable_encoder(value)
                        except (TypeError, ValueError):
                            del obbject.extra["metadata"].arguments[section][key]
                            continue

        return obbject