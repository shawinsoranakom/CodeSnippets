def reconnect(ssid=None, password=None, force_update=False):
    """Reconnect to the given network. If a connection to the network already exists,
    we can reconnect to it without providing the password (e.g. after a reboot).
    If no SSID is provided, we will try to reconnect to the last connected network.

    :param str ssid: SSID of the network to reconnect to (optional)
    :param str password: Password of the network to reconnect to (optional)
    :param bool force_update: Force connection, even if internet is already available through ethernet
    :return: True if reconnected successfully
    """
    if not force_update:
        timer = time.time() + 10  # Required on boot: wait 10 sec (see: https://github.com/odoo/odoo/pull/187862)
        while time.time() < timer:
            if get_ip():
                if is_access_point():
                    toggle_access_point(STOP)
                return True
            time.sleep(.5)

    if not ssid:
        return toggle_access_point(START)

    should_start_access_point_on_failure = is_access_point() or not get_ip()

    # Try to re-enable an existing connection, or set up a new persistent one
    if toggle_access_point(STOP) and not _nmcli(['con', 'up', ssid], sudo=True):
        _connect(ssid, password)

    connected_successfully = is_current(ssid)
    if not connected_successfully and should_start_access_point_on_failure:
        toggle_access_point(START)

    return connected_successfully