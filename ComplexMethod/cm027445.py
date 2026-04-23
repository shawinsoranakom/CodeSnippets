def get_aruba_data(self) -> dict[str, dict[str, str]] | None:
        """Retrieve data from Aruba Access Point and return parsed result."""

        connect = f"ssh {self.username}@{self.host}"
        ssh: pexpect.spawn[str] = pexpect.spawn(connect, encoding="utf-8")
        query = ssh.expect(
            [
                "password:",
                pexpect.TIMEOUT,
                pexpect.EOF,
                "continue connecting (yes/no)?",
                "Host key verification failed.",
                "Connection refused",
                "Connection timed out",
            ],
            timeout=120,
        )
        if query == 1:
            _LOGGER.error("Timeout")
            return None
        if query == 2:
            _LOGGER.error("Unexpected response from router")
            return None
        if query == 3:
            ssh.sendline("yes")
            ssh.expect("password:")
        elif query == 4:
            _LOGGER.error("Host key changed")
            return None
        elif query == 5:
            _LOGGER.error("Connection refused by server")
            return None
        elif query == 6:
            _LOGGER.error("Connection timed out")
            return None
        ssh.sendline(self.password)
        ssh.expect("#")
        ssh.sendline("show clients")
        ssh.expect("#")
        devices_result = (ssh.before or "").splitlines()
        ssh.sendline("exit")

        devices: dict[str, dict[str, str]] = {}
        for device in devices_result:
            if match := _DEVICES_REGEX.search(device):
                devices[match.group("ip")] = {
                    "ip": match.group("ip"),
                    "mac": match.group("mac").upper(),
                    "name": match.group("name"),
                }
        return devices