def _create_service_from_class(self, service_name: ServiceType) -> None:
        """Create a service from a registered service class (new plugin system)."""
        service_class = self.service_classes[service_name]
        logger.debug(f"Creating service from class: {service_name.value} -> {service_class.__name__}")

        # Inspect __init__ to determine dependencies
        init_signature = inspect.signature(service_class.__init__)
        dependencies = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == "self":
                continue

            # Try to resolve dependency from type hint first
            dependency_type = None
            if param.annotation != inspect.Parameter.empty:
                dependency_type = self._resolve_service_type_from_annotation(param.annotation)

            # If type hint didn't work, try to resolve from parameter name
            # E.g., param name "settings_service" -> ServiceType.SETTINGS_SERVICE
            if not dependency_type:
                try:
                    dependency_type = ServiceType(param_name)
                except ValueError:
                    # Not a valid service type - skip this parameter if it has a default
                    # Otherwise let it fail during instantiation
                    if param.default == inspect.Parameter.empty:
                        # No default, can't resolve - will fail during instantiation
                        pass
                    continue

            if dependency_type:
                # Check for circular dependency (service depending on itself)
                if dependency_type == service_name:
                    msg = f"Circular dependency detected: {service_name.value} depends on itself"
                    raise RuntimeError(msg)
                # Recursively create dependency if not exists
                # Note: Thread safety is handled by the caller's keyed lock context
                if dependency_type not in self.services:
                    self._create_service(dependency_type)
                dependencies[param_name] = self.services[dependency_type]

        # Create the service instance
        try:
            service_instance = service_class(**dependencies)
            # Don't call set_ready() here - let the service control its own ready state
            self.services[service_name] = service_instance
            logger.debug(f"Service created successfully: {service_name.value}")
        except Exception as exc:
            logger.exception(f"Failed to create service {service_name.value}: {exc}")
            raise