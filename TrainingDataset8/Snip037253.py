def get_component_path(self, name: str) -> Optional[str]:
        """Return the filesystem path for the component with the given name.

        If no such component is registered, or if the component exists but is
        being served from a URL, return None instead.
        """
        component = self._components.get(name, None)
        return component.abspath if component is not None else None