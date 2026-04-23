def uses_server_time(self):
        return self._fmt.find("{server_time}") >= 0