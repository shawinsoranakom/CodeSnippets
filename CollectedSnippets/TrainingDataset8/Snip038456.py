def get_url(host_ip: str) -> str:
    """Get the URL for any app served at the given host_ip.

    Parameters
    ----------
    host_ip : str
        The IP address of the machine that is running the Streamlit Server.

    Returns
    -------
    str
        The URL.
    """
    port = _get_browser_address_bar_port()
    base_path = config.get_option("server.baseUrlPath").strip("/")

    if base_path:
        base_path = "/" + base_path

    host_ip = host_ip.strip("/")

    return f"http://{host_ip}:{port}{base_path}"