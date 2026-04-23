def _get_server_key(self, connection_params, transport_type: str) -> str:
        """Generate a consistent server key based on connection parameters."""
        if transport_type == "stdio":
            if hasattr(connection_params, "command"):
                # Include command, args, and environment for uniqueness
                command_str = f"{connection_params.command} {' '.join(connection_params.args or [])}"
                env_str = str(sorted((connection_params.env or {}).items()))
                key_input = f"{command_str}|{env_str}"
                return f"stdio_{hash(key_input)}"
        elif transport_type == "streamable_http" and (
            isinstance(connection_params, dict) and "url" in connection_params
        ):
            # Include URL and headers for uniqueness
            url = connection_params["url"]
            headers = str(sorted((connection_params.get("headers", {})).items()))
            key_input = f"{url}|{headers}"
            return f"streamable_http_{hash(key_input)}"

        # Fallback to a generic key
        return f"{transport_type}_{hash(str(connection_params))}"