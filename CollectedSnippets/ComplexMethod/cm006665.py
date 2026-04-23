def get_factories(cls) -> list[ServiceFactory]:
        """Auto-discover and return all service factories."""
        from lfx.services.factory import ServiceFactory
        from lfx.services.schema import ServiceType

        service_names = [ServiceType(service_type).value.replace("_service", "") for service_type in ServiceType]
        base_module = "lfx.services"
        factories = []

        for name in service_names:
            try:
                module_name = f"{base_module}.{name}.factory"
                module = importlib.import_module(module_name)

                # Find all classes in the module that are subclasses of ServiceFactory
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if isinstance(obj, type) and issubclass(obj, ServiceFactory) and obj is not ServiceFactory:
                        factories.append(obj())
                        break

            except Exception:  # noqa: BLE001, S110
                # This is expected during initial service discovery - some services
                # may not have factories yet or depend on settings service being ready first
                # Intentionally suppressed to avoid startup noise - not an error condition
                pass

        return factories