def register_component(self, component: CustomComponent) -> None:
        """Register a CustomComponent.

        Parameters
        ----------
        component : CustomComponent
            The component to register.
        """

        # Validate the component's path
        abspath = component.abspath
        if abspath is not None and not os.path.isdir(abspath):
            raise StreamlitAPIException(f"No such component directory: '{abspath}'")

        with self._lock:
            existing = self._components.get(component.name)
            self._components[component.name] = component

        if existing is not None and component != existing:
            LOGGER.warning(
                "%s overriding previously-registered %s",
                component,
                existing,
            )

        LOGGER.debug("Registered component %s", component)