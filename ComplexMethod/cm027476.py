def as_dict(self) -> dict[str, Any]:
        """Return as dict."""
        addresses = None
        if self.addresses:
            addresses = {k: str(v) for k, v in self.addresses.items()}
        disk_usage = None
        if self.disk_usage:
            disk_usage = {k: str(v) for k, v in self.disk_usage.items()}
        fan_speed = None
        if self.fan_speed:
            fan_speed = {k: str(v) for k, v in self.fan_speed.items()}
        io_counters = None
        if self.io_counters:
            io_counters = {k: str(v) for k, v in self.io_counters.items()}
        temperatures = None
        if self.temperatures:
            temperatures = {k: str(v) for k, v in self.temperatures.items()}

        return {
            "addresses": addresses,
            "battery": str(self.battery),
            "boot_time": str(self.boot_time),
            "cpu_percent": str(self.cpu_percent),
            "disk_usage": disk_usage,
            "fan_speed": fan_speed,
            "io_counters": io_counters,
            "load": str(self.load),
            "memory": str(self.memory),
            "pressure": self.pressure,
            "process_fds": self.process_fds,
            "processes": str(self.processes),
            "swap": str(self.swap),
            "temperatures": temperatures,
        }