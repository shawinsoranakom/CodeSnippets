def set_components_path(cls, value):
        """Processes and updates the components path list, incorporating environment variable overrides.

        If the `LANGFLOW_COMPONENTS_PATH` environment variable is set and points to an existing path, it is
        appended to the provided list if not already present. If the input list is empty or missing, it is
        set to an empty list.
        """
        if os.getenv("LANGFLOW_COMPONENTS_PATH"):
            logger.debug("Adding LANGFLOW_COMPONENTS_PATH to components_path")
            langflow_component_path = os.getenv("LANGFLOW_COMPONENTS_PATH")
            if Path(langflow_component_path).exists() and langflow_component_path not in value:
                if isinstance(langflow_component_path, list):
                    for path in langflow_component_path:
                        if path not in value:
                            value.append(path)
                    logger.debug(f"Extending {langflow_component_path} to components_path")
                elif langflow_component_path not in value:
                    value.append(langflow_component_path)
                    logger.debug(f"Appending {langflow_component_path} to components_path")

        if not value:
            value = [BASE_COMPONENTS_PATH]
        elif isinstance(value, Path):
            value = [str(value)]
        elif isinstance(value, list):
            value = [str(p) if isinstance(p, Path) else p for p in value]
        return value