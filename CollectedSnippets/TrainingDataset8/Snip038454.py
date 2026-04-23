def _get_server_address_if_manually_set() -> Optional[str]:
    if config.is_manually_set("browser.serverAddress"):
        return url_util.get_hostname(config.get_option("browser.serverAddress"))
    return None