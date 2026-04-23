async def wrapper(  # pylint: disable=R0914,R0912  # noqa: PLR0912
        *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> OBBject | JSONResponse:
        user_settings: UserSettings = UserSettings.model_validate(
            kwargs.pop(
                "__authenticated_user_settings",
                UserService.read_from_file(),
            )
        )
        p = path.strip("/").replace("/", ".")
        defaults = (
            getattr(user_settings.defaults, "__dict__", {})
            .get("commands", {})
            .get(p, {})
        )
        standard_params = getattr(kwargs.pop("standard_params", None), "__dict__", {})
        extra_params = getattr(kwargs.pop("extra_params", None), "__dict__", {})

        if defaults:
            _ = defaults.pop("provider", None)

            if "chart" in defaults:
                kwargs["chart"] = defaults.pop("chart", False)

            if "chart_params" in defaults:
                extra_params["chart_params"] = defaults.pop("chart_params", {})

            for k, v in defaults.items():
                if k in standard_params and standard_params[k] is None:
                    standard_params[k] = v
                elif (k in standard_params and standard_params[k] is not None) or (
                    k in extra_params and extra_params[k] is not None
                ):
                    continue
                elif k not in extra_params or (
                    k in extra_params and extra_params[k] is None
                ):
                    extra_params[k] = v

        kwargs["standard_params"] = standard_params
        kwargs["extra_params"] = extra_params

        # We need to insert dependency objects that are
        # Added at the Router level and may not be part
        # of the function signature.
        dependencies = route.dependencies or []
        dep_names: list = []
        # Only inject the dependency if the endpoint
        # accepts undefined arguments.
        if has_var_kwargs and "kwargs" not in kwargs:
            kwargs["kwargs"] = {}

        for dep in dependencies:
            dep_callable = dep.dependency

            if not dep_callable:
                continue

            dep_name = getattr(dep_callable, "__name__", "") or ""
            dep_name = to_snake_case(dep_name).replace("get_", "")

            if has_var_kwargs and dep_name not in kwargs:
                kwargs["kwargs"][dep_name] = dep_callable()

            dep_names.append(dep_name)

        execute = partial(command_runner.run, path, user_settings)

        output = await execute(*args, **kwargs)

        if isinstance(output, OBBject):
            # This is where we check for `on_command_output` extensions
            mutated_output = getattr(output, "_extension_modified", False)
            results_only = getattr(output, "_results_only", False)
            try:
                if results_only is True:
                    content = output.model_dump(
                        exclude_unset=True, exclude_none=True
                    ).get("results", [])

                    return JSONResponse(
                        content=jsonable_encoder(content), status_code=200
                    )

                if (mutated_output and isinstance(output, OBBject)) or (
                    isinstance(output, OBBject) and no_validate
                ):
                    output.results = output.model_dump(
                        exclude_unset=True, exclude_none=True
                    ).get("results")

                    return JSONResponse(
                        content=jsonable_encoder(output), status_code=200
                    )
            except Exception as exc:  # pylint: disable=W0703
                raise OpenBBError(
                    f"Error serializing output for an extension-modified endpoint {path}: {exc}",
                ) from exc

            if not no_validate:
                return validate_output(output)

        return output