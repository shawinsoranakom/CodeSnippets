def update_data(self) -> dict[str, Any]:
        """To be extended by data update coordinators."""
        disks: dict[str, sdiskusage] = {}
        for argument in self._arguments:
            if self.update_subscribers[("disks", argument)] or self._initial_update:
                try:
                    usage: sdiskusage = self._psutil.disk_usage(argument)
                    _LOGGER.debug("sdiskusagefor %s: %s", argument, usage)
                except PermissionError as err:
                    _LOGGER.warning(
                        "No permission to access %s, error %s", argument, err
                    )
                except OSError as err:
                    _LOGGER.warning("OS error for %s, error %s", argument, err)
                else:
                    disks[argument] = usage

        swap: sswap | None = None
        if self.update_subscribers[("swap", "")] or self._initial_update:
            swap = self._psutil.swap_memory()
            _LOGGER.debug("sswap: %s", swap)

        memory = None
        if self.update_subscribers[("memory", "")] or self._initial_update:
            memory = self._psutil.virtual_memory()
            _LOGGER.debug("memory: %s", memory)
            memory = VirtualMemory(
                memory.total, memory.available, memory.percent, memory.used, memory.free
            )

        io_counters: dict[str, snetio] | None = None
        if self.update_subscribers[("io_counters", "")] or self._initial_update:
            io_counters = self._psutil.net_io_counters(pernic=True)
            _LOGGER.debug("io_counters: %s", io_counters)

        addresses: dict[str, list[snicaddr]] | None = None
        if self.update_subscribers[("addresses", "")] or self._initial_update:
            addresses = self._psutil.net_if_addrs()
            _LOGGER.debug("ip_addresses: %s", addresses)

        if self._initial_update:
            # Boot time only needs to refresh on first pass
            self.boot_time = dt_util.utc_from_timestamp(
                self._psutil.boot_time(), tz=dt_util.get_default_time_zone()
            )
            _LOGGER.debug("boot time: %s", self.boot_time)

        selected_processes: list[Process] = []
        process_fds: dict[str, int] = {}
        if self.update_subscribers[("processes", "")] or self._initial_update:
            processes = self._psutil.process_iter()
            _LOGGER.debug("processes: %s", processes)
            user_options: list[str] = self.config_entry.options.get(
                BINARY_SENSOR_DOMAIN, {}
            ).get(CONF_PROCESS, [])
            for process in processes:
                try:
                    if (process_name := process.name()) in user_options:
                        selected_processes.append(process)
                        process_fds[process_name] = (
                            process_fds.get(process_name, 0) + process.num_fds()
                        )

                except PROCESS_ERRORS as err:
                    if not hasattr(err, "pid") or not hasattr(err, "name"):
                        _LOGGER.warning(
                            "Failed to load process: %s",
                            str(err),
                        )
                    else:
                        _LOGGER.warning(
                            "Failed to load process with ID: %s, old name: %s",
                            err.pid,
                            err.name,
                        )
                    continue
                except OSError as err:
                    _LOGGER.warning(
                        "OS error getting file descriptor count for process %s: %s",
                        process.pid if hasattr(process, "pid") else "unknown",
                        err,
                    )

        temps: dict[str, list[shwtemp]] = {}
        if self.update_subscribers[("temperatures", "")] or self._initial_update:
            try:
                temps = self._psutil.sensors_temperatures()
                _LOGGER.debug("temps: %s", temps)
            except AttributeError:
                _LOGGER.debug("OS does not provide temperature sensors")

        fan_speed: dict[str, int] = {}
        if self.update_subscribers[("fan_speed", "")] or self._initial_update:
            try:
                fan_sensors = self._psutil.sensors_fans()
                fan_speed = read_fan_speed(fan_sensors)
                _LOGGER.debug("fan_speed: %s", fan_speed)
            except AttributeError:
                _LOGGER.debug("OS does not provide fan sensors")

        battery: sbattery | None = None
        if self.update_subscribers[("battery", "")] or self._initial_update:
            try:
                battery = self._psutil.sensors_battery()
                _LOGGER.debug("battery: %s", battery)
            except (FileNotFoundError, PermissionError) as err:
                _LOGGER.debug("OS error when accessing battery sensors: %s", err)
            except AttributeError:
                _LOGGER.debug("OS does not provide battery sensors")

        pressure: dict[str, Any] = {}
        if self.update_subscribers[("pressure", "")] or self._initial_update:
            pressure = get_all_pressure_info()
            _LOGGER.debug("pressure: %s", pressure)

        return {
            "addresses": addresses,
            "battery": battery,
            "boot_time": self.boot_time,
            "disks": disks,
            "fan_speed": fan_speed,
            "io_counters": io_counters,
            "memory": memory,
            "pressure": pressure,
            "process_fds": process_fds,
            "processes": selected_processes,
            "swap": swap,
            "temperatures": temps,
        }