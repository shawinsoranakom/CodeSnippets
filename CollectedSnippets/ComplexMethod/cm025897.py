def get(self, request: web.Request) -> str | None:
        """Handle Torque data request."""
        data = request.query

        if self.email is not None and self.email != data[SENSOR_EMAIL_FIELD]:
            return None

        names = {}
        units = {}
        for key in data:
            is_name = NAME_KEY.match(key)
            is_unit = UNIT_KEY.match(key)
            is_value = VALUE_KEY.match(key)

            if is_name:
                pid = convert_pid(is_name.group(1))
                names[pid] = data[key]
            elif is_unit:
                pid = convert_pid(is_unit.group(1))

                temp_unit = data[key]
                if "\\xC2\\xB0" in temp_unit:
                    temp_unit = temp_unit.replace("\\xC2\\xB0", DEGREE)

                units[pid] = temp_unit
            elif is_value:
                pid = convert_pid(is_value.group(1))
                if pid in self.sensors:
                    self.sensors[pid].async_on_update(data[key])

        new_sensor_entities: list[TorqueSensor] = []
        for pid, name in names.items():
            if pid not in self.sensors:
                torque_sensor_entity = TorqueSensor(
                    ENTITY_NAME_FORMAT.format(self.vehicle, name), units.get(pid)
                )
                new_sensor_entities.append(torque_sensor_entity)
                self.sensors[pid] = torque_sensor_entity

        if new_sensor_entities:
            self.async_add_entities(new_sensor_entities)

        return "OK!"