def server_port_is_manually_set() -> bool:
    return config.is_manually_set("server.port")