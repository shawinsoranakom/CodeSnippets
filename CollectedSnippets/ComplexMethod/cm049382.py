def get_homepage_data(self):
        network_interfaces = []
        if IS_RPI:
            ssid = wifi.get_current() or wifi.get_access_point_ssid()
            for iface_id in netifaces.interfaces():
                if iface_id == 'lo':
                    continue  # Skip loopback interface (127.0.0.1)

                is_wifi = 'wlan' in iface_id
                network_interfaces.extend([{
                    'id': iface_id,
                    'is_wifi': is_wifi,
                    'ssid': ssid if is_wifi else None,
                    'ip': conf.get('addr', 'No Internet'),
                } for conf in netifaces.ifaddresses(iface_id).get(netifaces.AF_INET, [])])

        devices = [{
            'name': device.device_name,
            'type': device.device_type,
            'identifier': device.device_identifier,
            'connection': device.device_connection,
        } for device in iot_devices.values()]
        devices += list(unsupported_devices.values())

        def device_type_key(device):
            return device['type']

        grouped_devices = {
            device_type: list(devices)
            for device_type, devices in groupby(sorted(devices, key=device_type_key), device_type_key)
        }

        six_terminal = helpers.get_conf('six_payment_terminal') or 'Not Configured'
        network_qr_codes = wifi.generate_network_qr_codes() if IS_RPI else {}
        odoo_server_url = helpers.get_odoo_server_url() or ''
        odoo_uptime_seconds = time.monotonic() - helpers.odoo_start_time
        system_uptime_seconds = time.monotonic() - helpers.system_start_time

        return json.dumps({
            'db_uuid': helpers.get_conf('db_uuid'),
            'enterprise_code': helpers.get_conf('enterprise_code'),
            'ip': helpers.get_ip(),
            'identifier': helpers.get_identifier(),
            'mac_address': helpers.get_mac_address(),
            'devices': grouped_devices,
            'server_status': odoo_server_url,
            'pairing_code': connection_manager.pairing_code,
            'new_database_url': connection_manager.new_database_url,
            'pairing_code_expired': connection_manager.pairing_code_expired and not odoo_server_url,
            'six_terminal': six_terminal,
            'is_access_point_up': IS_RPI and wifi.is_access_point(),
            'network_interfaces': network_interfaces,
            'version': helpers.get_version(),
            'system': IOT_SYSTEM,
            'odoo_uptime_seconds': odoo_uptime_seconds,
            'system_uptime_seconds': system_uptime_seconds,
            'certificate_end_date': certificate.get_certificate_end_date(),
            'wifi_ssid': helpers.get_conf('wifi_ssid'),
            'qr_code_wifi': network_qr_codes.get('qr_wifi'),
            'qr_code_url': network_qr_codes.get('qr_url'),
        })