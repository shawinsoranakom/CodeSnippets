def server_address_is_unix_socket() -> bool:
    address = config.get_option("server.address")
    return address is not None and address.startswith(UNIX_SOCKET_PREFIX)