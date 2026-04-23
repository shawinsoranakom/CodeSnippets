def _get_provider(
        self, choice: str | None, command: str, default_priority: tuple[str, ...]
    ) -> str:
        """Get the provider to use in execution.

        If no choice is specified, the configured priority list is used. A provider is used
        when all of its required credentials are populated.

        Parameters
        ----------
        choice: Optional[str]
            The provider choice, for example 'fmp'.
        command: str
            The command to get the provider for, for example 'equity.price.historical'
        default_priority: Tuple[str, ...]
            A tuple of available providers for the given command to use as default priority list.

        Returns
        -------
        str
            The provider to use in the command.

        Raises
        ------
        OpenBBError
            Raises error when all the providers in the priority list failed.
        """
        if choice is None:
            commands = self._command_runner.user_settings.defaults.commands
            providers = (
                commands.get(command, {}).get("provider", []) or default_priority
            )
            tries = []
            if len(providers) == 1:
                return providers[0]
            for p in providers:
                result = self._check_credentials(p)
                if result:
                    return p
                if result is False:
                    tries.append((p, "missing credentials"))
                else:
                    tries.append((p, f"not installed, please install openbb-{p}"))

            msg = "\n  ".join([f"* '{pair[0]}' -> {pair[1]}" for pair in tries])
            raise OpenBBError(f"Provider fallback failed.\n[Providers]\n  {msg}")
        return choice