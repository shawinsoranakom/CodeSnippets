def _load_entities(self):
        sensor_info = []
        for pidx, printer in enumerate(self.printers):
            for sensor_type in self.sensors:
                info = {}
                info["sensor_type"] = sensor_type
                info["printer_id"] = pidx
                info["name"] = printer.slug
                info["printer_name"] = self.conf_name

                known = f"{printer.slug}-{sensor_type}"
                if known in self._known_entities:
                    continue

                methods = API_PRINTER_METHODS[sensor_type]
                if "temp_data" in methods.state.values():
                    prop_data = getattr(printer, methods.attribute or "")
                    if prop_data is None:
                        continue
                    for idx, _ in enumerate(prop_data):
                        prop_info = info.copy()
                        prop_info["temp_id"] = idx
                        sensor_info.append(prop_info)
                else:
                    info["temp_id"] = None
                    sensor_info.append(info)
                self._known_entities.add(known)

        if not sensor_info:
            return
        load_platform(
            self._hass, "sensor", DOMAIN, {"sensors": sensor_info}, self.config
        )