def set_up_printer_in_cups(self, device: dict) -> bool:
        """Configure detected printer in cups: ppd files, name, info, groups, ...

        :param dict device: printer device to configure in cups (detected but not added)
        """
        if device.get("already-configured"):
            return True
        fallback_model = device.get('device-make-and-model', "")
        model = next((
            device_id.split(":")[1] for device_id in device.get('device-id', "").split(";")
            if any(key in device_id for key in ['MDL', 'MODEL'])
        ), fallback_model)
        model = re.sub(r"[\(].*?[\)]", "", model).strip()

        ppdname_argument = next(
            ({"ppdname": ppd} for ppd in self.PPDs if model and model in self.PPDs[ppd]['ppd-product']),
            {"ppdname": "everywhere"} if device.get("ipp_ready") else {}
        )

        try:
            self.conn.addPrinter(name=device['identifier'], device=device['url'], **ppdname_argument)
            self.conn.setPrinterInfo(device['identifier'], device['device-make-and-model'])
            self.conn.enablePrinter(device['identifier'])
            self.conn.acceptJobs(device['identifier'])
            self.conn.setPrinterUsersAllowed(device['identifier'], ['all'])
            self.conn.addPrinterOptionDefault(device['identifier'], "usb-no-reattach", "true")
            self.conn.addPrinterOptionDefault(device['identifier'], "usb-unidir", "true")
            return True
        except IPPError:
            _logger.exception("Failed to add printer '%s'", device['identifier'])
            return False