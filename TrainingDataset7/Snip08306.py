def client_servers(self):
        output = []
        for server in self._servers:
            output.append(server.removeprefix("unix:"))
        return output