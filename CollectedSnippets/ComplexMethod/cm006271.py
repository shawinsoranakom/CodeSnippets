def import_all_services_into_a_dict():
    # Services are all in langflow.services.{service_name}.service
    # and are subclass of Service
    # We want to import all of them and put them in a dict
    # to use as globals
    from langflow.services.base import Service

    services = {}
    for service_type in ServiceType:
        try:
            service_name = ServiceType(service_type).value.replace("_service", "")

            # Special handling for mcp_composer which is now in lfx module
            if service_name == "mcp_composer":
                module_name = f"lfx.services.{service_name}.service"
            else:
                module_name = f"langflow.services.{service_name}.service"

            module = importlib.import_module(module_name)
            services.update(
                {
                    name: obj
                    for name, obj in inspect.getmembers(module, inspect.isclass)
                    if isinstance(obj, type) and issubclass(obj, Service) and obj is not Service
                }
            )
        except Exception as exc:
            logger.exception(exc)
            msg = "Could not initialize services. Please check your settings."
            raise RuntimeError(msg) from exc
    # Import settings and auth base from lfx (used in type hints but not langflow Service subclasses)
    from lfx.services.auth.base import BaseAuthService
    from lfx.services.settings.service import SettingsService

    services["BaseAuthService"] = BaseAuthService
    services["SettingsService"] = SettingsService
    return services