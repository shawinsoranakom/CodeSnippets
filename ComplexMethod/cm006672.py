def validate_runtime_port(cls, value):
        """Parse port from Kubernetes service discovery env vars.

        Kubernetes auto-creates env vars like LANGFLOW_RUNTIME_PORT=tcp://<ip>:<port>
        for services, which collides with the LANGFLOW_ env prefix. Extract the port
        number from URL-like values instead of failing.
        """
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.isdigit():
                return int(value)
            if "://" in value:
                from urllib.parse import urlparse

                try:
                    parsed_port = urlparse(value).port
                except ValueError:
                    return None
                if parsed_port is not None:
                    return parsed_port
        return None