def get_options_map(
        self, command: str, *, snake_case: bool = False
    ) -> dict[str, str]:
        """Get the available options for a command."""
        capabilities = self.capabilities.get(command, {})

        if TYPE_CHECKING:
            assert isinstance(capabilities, dict)
            assert isinstance(capabilities.get("parameter", {}), dict)
            assert isinstance(capabilities.get("parameter", {}).get("read", {}), dict)

        values = list(capabilities.get("parameter", {}).get("read", {}).values())

        options = {v: v.translate(TRANSLATIONS) for v in values}
        if snake_case:
            return {k: v.replace("-", "_") for k, v in options.items()}
        return options