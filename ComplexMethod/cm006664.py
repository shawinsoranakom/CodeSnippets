def _create_service_from_factory(self, service_name: ServiceType, default: ServiceFactory | None = None) -> None:
        """Create a service from a factory (old system)."""
        self._validate_service_creation(service_name, default)

        if service_name == ServiceType.SETTINGS_SERVICE:
            from lfx.services.settings.factory import SettingsServiceFactory

            factory = SettingsServiceFactory()
            if factory not in self.factories:
                self.register_factory(factory)
        else:
            factory = self.factories.get(service_name)

        # Create dependencies first
        if factory is None and default is not None:
            self.register_factory(default)
            factory = default
        if factory is None:
            msg = f"No factory registered for {service_name}"
            raise NoFactoryRegisteredError(msg)
        for dependency in factory.dependencies:
            if dependency not in self.services:
                self._create_service(dependency)

        # Collect the dependent services
        dependent_services = {dep.value: self.services[dep] for dep in factory.dependencies}

        # Create the actual service
        self.services[service_name] = self.factories[service_name].create(**dependent_services)
        self.services[service_name].set_ready()