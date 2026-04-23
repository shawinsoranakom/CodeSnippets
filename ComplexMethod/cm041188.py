def require_service(self, _: HandlerChain, context: RequestContext, response: Response):
        if not context.service:
            return

        service_name: str = context.service.service_name
        if service_name in self.loaded_services:
            return

        if not self.service_manager.exists(service_name):
            raise NotImplementedError
        elif not is_api_enabled(service_name):
            raise NotImplementedError(
                f"Service '{service_name}' is not enabled. Please check your 'SERVICES' configuration variable."
            )

        request_router = self.service_request_router
        try:
            # Ensure the Service is loaded and set to ServiceState.RUNNING if not in an erroneous state.
            service_plugin: Service = self.service_manager.require(service_name)
        except PluginDisabled as e:
            if e.reason == "This feature is not part of the active license agreement":
                raise PluginNotIncludedInUserLicenseError()
            raise

        with self.service_locks[context.service.service_name]:
            # try again to avoid race conditions
            if service_name in self.loaded_services:
                return
            self.loaded_services.add(service_name)
            if isinstance(service_plugin, Service):
                request_router.add_skeleton(service_plugin.skeleton)
            else:
                LOG.warning(
                    "found plugin for '%s', but cannot attach service plugin of type '%s'",
                    service_name,
                    type(service_plugin),
                )