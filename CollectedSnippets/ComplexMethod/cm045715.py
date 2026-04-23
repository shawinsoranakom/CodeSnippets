def __post_init__(self):
        if self.transport not in ["streamable-http", "stdio"]:
            raise ValueError(
                f"Invalid transport type: {self.transport}. "
                "Must be one of 'streamable-http' or 'stdio'."
            )
        if self.transport == "stdio":
            warnings.warn(
                "The 'stdio' transport is unstable and experimental. "
                "It may change or be removed in future releases.",
                stacklevel=2,
            )
            if self.host is not None or self.port is not None:
                raise ValueError(
                    "Host and port cannot be set when transport is 'stdio'."
                )
        elif self.transport == "streamable-http":
            if self.host is None or self.port is None:
                raise ValueError(
                    "Host and port must be set when transport is 'streamable-http'."
                )