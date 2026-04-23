def update(self) -> None:
        """Update the states of Neato Vacuums."""
        _LOGGER.debug("Running Neato Vacuums update for '%s'", self.entity_id)
        try:
            if self._robot_stats is None:
                self._robot_stats = self.robot.get_general_info().json().get("data")
        except NeatoRobotException:
            _LOGGER.warning("Couldn't fetch robot information of %s", self.entity_id)

        try:
            self._state = self.robot.state
        except NeatoRobotException as ex:
            if self._attr_available:  # print only once when available
                _LOGGER.error(
                    "Neato vacuum connection error for '%s': %s", self.entity_id, ex
                )
            self._state = None
            self._attr_available = False
            return

        if self._state is None:
            return
        self._attr_available = True
        _LOGGER.debug("self._state=%s", self._state)
        if "alert" in self._state:
            robot_alert = ALERTS.get(self._state["alert"])
        else:
            robot_alert = None
        if self._state["state"] == 1:
            if self._state["details"]["isCharging"]:
                self._attr_activity = VacuumActivity.DOCKED
                self._status_state = "Charging"
            elif (
                self._state["details"]["isDocked"]
                and not self._state["details"]["isCharging"]
            ):
                self._attr_activity = VacuumActivity.DOCKED
                self._status_state = "Docked"
            else:
                self._attr_activity = VacuumActivity.IDLE
                self._status_state = "Stopped"

            if robot_alert is not None:
                self._status_state = robot_alert
        elif self._state["state"] == 2:
            if robot_alert is None:
                self._attr_activity = VacuumActivity.CLEANING
                self._status_state = (
                    f"{MODE.get(self._state['cleaning']['mode'])} "
                    f"{ACTION.get(self._state['action'])}"
                )
                if (
                    "boundary" in self._state["cleaning"]
                    and "name" in self._state["cleaning"]["boundary"]
                ):
                    self._status_state += (
                        f" {self._state['cleaning']['boundary']['name']}"
                    )
            else:
                self._status_state = robot_alert
        elif self._state["state"] == 3:
            self._attr_activity = VacuumActivity.PAUSED
            self._status_state = "Paused"
        elif self._state["state"] == 4:
            self._attr_activity = VacuumActivity.ERROR
            self._status_state = ERRORS.get(self._state["error"])

        self._attr_battery_level = self._state["details"]["charge"]

        if self._mapdata is None or not self._mapdata.get(self._robot_serial, {}).get(
            "maps", []
        ):
            return

        mapdata: dict[str, Any] = self._mapdata[self._robot_serial]["maps"][0]
        self._clean_time_start = mapdata["start_at"]
        self._clean_time_stop = mapdata["end_at"]
        self._clean_area = mapdata["cleaned_area"]
        self._clean_susp_charge_count = mapdata["suspended_cleaning_charging_count"]
        self._clean_susp_time = mapdata["time_in_suspended_cleaning"]
        self._clean_pause_time = mapdata["time_in_pause"]
        self._clean_error_time = mapdata["time_in_error"]
        self._clean_battery_start = mapdata["run_charge_at_start"]
        self._clean_battery_end = mapdata["run_charge_at_end"]
        self._launched_from = mapdata["launched_from"]

        if (
            self._robot_has_map
            and self._state
            and self._state["availableServices"]["maps"] != "basic-1"
            and self._robot_maps
        ):
            allmaps: dict = self._robot_maps[self._robot_serial]
            _LOGGER.debug(
                "Found the following maps for '%s': %s", self.entity_id, allmaps
            )
            self._robot_boundaries = []  # Reset boundaries before refreshing boundaries
            for maps in allmaps:
                try:
                    robot_boundaries = self.robot.get_map_boundaries(maps["id"]).json()
                except NeatoRobotException as ex:
                    _LOGGER.error(
                        "Could not fetch map boundaries for '%s': %s",
                        self.entity_id,
                        ex,
                    )
                    return

                _LOGGER.debug(
                    "Boundaries for robot '%s' in map '%s': %s",
                    self.entity_id,
                    maps["name"],
                    robot_boundaries,
                )
                if "boundaries" in robot_boundaries["data"]:
                    self._robot_boundaries += robot_boundaries["data"]["boundaries"]
                    _LOGGER.debug(
                        "List of boundaries for '%s': %s",
                        self.entity_id,
                        self._robot_boundaries,
                    )