def _printer_status_content(self):
        """Formats the status information of the IoT Box into a title and a body.

        :return: The title and the body of the status ticket
        :rtype: tuple of bytes
        """
        wlan = identifier = homepage = pairing_code = mac_address = ""
        iot_status = self._get_iot_status()

        wan_quality = helpers.check_network("www.odoo.com")
        to_gateway_quality = helpers.check_network()
        to_printer_quality = helpers.check_network(self.ip) if self.ip else None

        if iot_status["pairing_code"]:
            pairing_code = (
                '\nOdoo not connected\n'
                'Go to the IoT app, click "Connect",\n'
                'Pairing Code: %s\n' % iot_status["pairing_code"]
            )

        if iot_status['ssid']:
            wlan = '\nWireless network:\n%s\n' % iot_status["ssid"]

        ips = iot_status["ips"]
        if len(ips) == 0:
            ip = (
                "\nERROR: Could not connect to LAN\n\nPlease check that the IoT Box is correc-\ntly connected with a "
                "network cable,\n that the LAN is setup with DHCP, and\nthat network addresses are available"
            )
        elif len(ips) == 1:
            ip = '\nIoT Box IP Address:\n%s\n' % ips[0]
        else:
            ip = '\nIoT Box IP Addresses:\n%s\n' % '\n'.join(ips)

        if len(ips) == 0:
            network_quality = ""
        else:
            network_quality = "\nNetwork quality:\n - To Odoo server: %s\n" % wan_quality
            if to_gateway_quality:
                network_quality += " - To Modem: %s\n" % to_gateway_quality
            if to_printer_quality:
                network_quality += " - To Printer (%s): %s\n" % (self.ip, to_printer_quality)

        if len(ips) >= 1:
            identifier = '\nIdentifier:\n%s\n' % iot_status["identifier"]
            mac_address = '\nMac Address:\n%s\n' % iot_status["mac_address"]
            homepage = '\nIoT Box Homepage:\nhttp://%s:8069\n' % ips[0]

        title = b'IoT Box Connected' if helpers.get_odoo_server_url() else b'IoT Box Status'
        body = pairing_code + wlan + identifier + mac_address + ip + network_quality + homepage

        return title, body.encode()