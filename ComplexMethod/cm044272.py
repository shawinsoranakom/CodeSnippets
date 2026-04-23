def __init__(
        self,
        name: str,
        credentials: list[str] | None = None,
        description: str | None = None,
        on_command_output: bool = False,
        command_output_paths: list[str] | None = None,
        immutable: bool = True,
        results_only: bool = False,
    ) -> None:
        """Initialize the extension.

        Parameters
        ----------
        name : str
            Name of the extension.
        credentials : list[str], optional
            List of required credentials, by default None
        description: Optional[str]
            Extension description.
        on_command_output : bool, optional
            Whether the extension acts on command output, by default False
        command_output_paths : list[str], optional
            List of endpoint paths the extension acts on, where None means all, by default None.
        immutable : bool, optional
            Whether the function output is immutable, by default True.
        results_only : bool, optional
            Whether the extension returns only the results instead of the OBBject, by default False.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.service.system_service import SystemService

        self.name = name
        self.credentials = credentials or []
        self.description = description
        self.on_command_output = on_command_output
        self.command_output_paths = command_output_paths or []
        self.immutable = immutable
        self.results_only = results_only

        # This must be explicitly enabled.
        if self.on_command_output is False and (
            self.command_output_paths
            or self.results_only is True
            or self.immutable is False
        ):
            raise ValueError(
                "OBBject Extension Error -> 'on_command_output' must be set as True when"
                + " 'command_output_paths', 'results_only' or 'immutable' is set.",
            )

        # The user must explicitly enable OBBject extensions that act on command output.
        if (
            self.on_command_output
            and not SystemService().system_settings.allow_on_command_output
        ):
            raise RuntimeError(
                "OBBject Extension Error -> \n\n"
                + "An OBBject extension that acts on command output is installed "
                + "but has not been enabled in `system_settings.json`.\n\n"
                + "Set `allow_on_command_output` to True to enable it.\n"
                + "Or, set the environment variable `OPENBB_ALLOW_ON_COMMAND_OUTPUT` to True."
                + "\n\nProceed with caution as this may have security implications.\n\n"
                + "Ensure the extension is installed from a trusted source.\n\n",
            )

        # The user must explicitly enable OBBject extensions that modify output.
        if (
            self.on_command_output
            and self.immutable is False
            and not SystemService().system_settings.allow_mutable_extensions
        ):
            raise RuntimeError(
                "OBBject Extension Error -> \n\n"
                + "An OBBject extension that modifies the output is installed "
                + "but has not been enabled in `system_settings.json`.\n\n"
                + "Set `allow_mutable_extensions` to True to enable it.\n"
                + "Or, set the environment variable `OPENBB_ALLOW_MUTABLE_EXTENSIONS` to True."
                + "\n\nProceed with caution as this may have security implications.\n\n"
                + "Ensure the extension is installed from a trusted source.\n\n",
            )