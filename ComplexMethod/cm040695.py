def require(self, name: str) -> Service:
        """
        High level function that always returns a running service, or raises an error. If the service is in a state
        that it could be transitioned into a running state, then invoking this function will attempt that transition,
        e.g., by starting the service if it is available.
        """
        container = self.get_service_container(name)

        if not container:
            raise ValueError(f"no such service {name}")

        if container.state == ServiceState.STARTING:
            if not poll_condition(lambda: container.state != ServiceState.STARTING, timeout=30):
                raise TimeoutError(f"gave up waiting for service {name} to start")

        if container.state == ServiceState.STOPPING:
            if not poll_condition(lambda: container.state == ServiceState.STOPPED, timeout=30):
                raise TimeoutError(f"gave up waiting for service {name} to stop")

        with container.lock:
            if container.state == ServiceState.DISABLED:
                raise ServiceDisabled(f"service {name} is disabled")

            if container.state == ServiceState.RUNNING:
                return container.service

            if container.state == ServiceState.ERROR:
                # raise any capture error
                raise container.errors[-1]

            if container.state == ServiceState.AVAILABLE or container.state == ServiceState.STOPPED:
                if container.start():
                    return container.service
                else:
                    raise container.errors[-1]

        raise ServiceStateException(
            f"service {name} is not ready ({container.state}) and could not be started"
        )