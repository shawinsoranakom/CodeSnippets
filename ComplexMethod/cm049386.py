def deduplicate_printers(self, discovered_printers):
        result = []
        sorted_printers = sorted(
            discovered_printers.values(), key=lambda printer: (str(printer.get('ip')), printer["identifier"])
        )

        for ip, printers_with_same_ip in groupby(sorted_printers, lambda printer: printer.get('ip')):
            already_registered_identifier = next((
                identifier for identifier, device in iot_devices.items()
                if device.device_type == 'printer' and ip and ip == device.ip
            ), None)
            if already_registered_identifier:
                result += next(
                    ([p] for p in printers_with_same_ip if p['identifier'] == already_registered_identifier), []
                )
                continue

            printers_with_same_ip = list(printers_with_same_ip)
            is_ipp_ready = any(p['identifier'].startswith("ipp") for p in printers_with_same_ip)
            if ip is None or len(printers_with_same_ip) == 1:
                printers_with_same_ip[0]["is_ipp_ready"] = is_ipp_ready
                result += printers_with_same_ip
                continue

            chosen_printer = next((
                printer for printer in printers_with_same_ip
                if 'CMD:' in printer['device-id'] or 'ZPL' in printer['device-id']
            ), printers_with_same_ip[0])

            chosen_printer["ipp_ready"] = is_ipp_ready
            result.append(chosen_printer)

        return {
            printer['identifier']: printer
            for printer in result
            if self.set_up_printer_in_cups(printer)
        }