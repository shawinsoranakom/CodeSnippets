def run(self):
        """Thread that will load interfaces and drivers and contact the odoo server
        with the updates. It will also reconnect to the Wi-Fi if the connection is lost.
        """
        if IS_RPI:
            # ensure that the root filesystem is writable retro compatibility (TODO: remove this in 19.0)
            subprocess.run(["sudo", "mount", "-o", "remount,rw", "/"], check=False)
            subprocess.run(["sudo", "mount", "-o", "remount,rw", "/root_bypass_ramdisks/"], check=False)

            wifi.reconnect(helpers.get_conf('wifi_ssid'), helpers.get_conf('wifi_password'))

        helpers.start_nginx_server()
        _logger.info("IoT Box Image version: %s", helpers.get_version(detailed_version=True))
        upgrade.check_git_branch()

        if IS_RPI and helpers.get_odoo_server_url():
            helpers.generate_password()

        certificate.ensure_validity()

        # We first add the IoT Box to the connected DB because IoT handlers cannot be downloaded if
        # the identifier of the Box is not found in the DB. So add the Box to the DB.
        self._send_all_devices()
        helpers.download_iot_handlers()
        helpers.load_iot_handlers()

        for interface in interfaces.values():
            interface().start()

        # Set scheduled actions
        schedule.every().day.at("00:00").do(certificate.ensure_validity)
        schedule.every().day.at("00:00").do(helpers.reset_log_level)
        schedule.every().day.at("00:00").do(upgrade.check_git_branch)

        # Set up the websocket connection
        ws_client = WebsocketClient(self.ws_channel)
        if ws_client:
            ws_client.start()

        # Check every 3 seconds if the list of connected devices has changed and send the updated
        # list to the connected DB.
        while 1:
            try:
                if self._get_changes_to_send():
                    self._send_all_devices()
                if IS_RPI and helpers.get_ip() != '10.11.12.1':
                    wifi.reconnect(helpers.get_conf('wifi_ssid'), helpers.get_conf('wifi_password'))
                time.sleep(3)
                schedule.run_pending()
            except Exception:
                # No matter what goes wrong, the Manager loop needs to keep running
                _logger.exception("Manager loop unexpected error")