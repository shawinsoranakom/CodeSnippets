def _assert_sensor(self, name, state=None, cls=None, unit=None, disabled=False):
        sensor = self.hass.states.get(name)
        if disabled:
            assert sensor is None
            return

        assert sensor.state == state
        if cls:
            assert sensor.attributes["device_class"] == cls
        if unit:
            assert sensor.attributes["unit_of_measurement"] == unit

        assert sensor.attributes["attribution"] == "Data provided by Picnic"