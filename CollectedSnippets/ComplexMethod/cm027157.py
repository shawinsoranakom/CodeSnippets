def update(self) -> None:
        """Process new events from panel."""
        try:
            part = self._alarm.list_partitions()[0]
            zones = self._alarm.list_zones()
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error(
                "Unable to connect to %(host)s: %(reason)s",
                {"host": self._url, "reason": ex},
            )
            self._attr_alarm_state = None
            zones = []
        except IndexError:
            _LOGGER.error("NX584 reports no partitions")
            self._attr_alarm_state = None
            zones = []

        bypassed = False
        for zone in zones:
            if zone["bypassed"]:
                _LOGGER.debug(
                    "Zone %(zone)s is bypassed, assuming HOME",
                    {"zone": zone["number"]},
                )
                bypassed = True
                break

        if not part["armed"]:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
        elif bypassed:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        else:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY

        for flag in part["condition_flags"]:
            if flag == "Siren on":
                self._attr_alarm_state = AlarmControlPanelState.TRIGGERED