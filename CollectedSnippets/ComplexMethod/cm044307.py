def _run(self, *args, **kwargs) -> Any:
        """Run a command in the container."""
        endpoint = args[0][1:].replace("/", ".") if args else ""
        defaults = self._command_runner.user_settings.defaults.commands

        if endpoint and defaults and defaults.get(endpoint):
            default_params = {
                k: v for k, v in defaults[endpoint].items() if k != "provider"
            }
            for k, v in default_params.items():
                if k == "chart" and v is True:
                    kwargs["chart"] = True
                elif (
                    k in kwargs["standard_params"]
                    and kwargs["standard_params"][k] is None
                ):
                    kwargs["standard_params"][k] = v
                elif (
                    k in kwargs["extra_params"] and kwargs["extra_params"][k] is None
                ) or k not in kwargs["extra_params"]:
                    kwargs["extra_params"][k] = v

        obbject = self._command_runner.sync_run(*args, **kwargs)

        results_only = getattr(obbject, "_results_only", False)

        if results_only is True:
            content = obbject.model_dump(exclude_unset=True).get("results", [])
            return content

        output_type = self._command_runner.user_settings.preferences.output_type

        if output_type == "OBBject":
            return obbject

        return getattr(obbject, "to_" + output_type)()