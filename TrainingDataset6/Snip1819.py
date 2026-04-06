def _get_socket_path():
    return os.environ.get(const.SHELL_LOGGER_SOCKET_ENV)