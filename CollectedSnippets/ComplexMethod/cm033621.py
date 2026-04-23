def get(self, tries: int = 3, sleep: int = 15, always_raise_on: t.Optional[list[int]] = None) -> t.Optional[InstanceConnection]:
        """Get instance connection information."""
        if not self.started:
            display.info(f'Skipping invalid {self.label} instance.', verbosity=1)
            return None

        if not always_raise_on:
            always_raise_on = []

        if self.connection and self.connection.running:
            return self.connection

        while True:
            tries -= 1
            response = self.client.get(self._uri)

            if response.status_code == 200:
                break

            error = self._create_http_error(response)

            if not tries or response.status_code in always_raise_on:
                raise error

            display.warning(f'{error}. Trying again after {sleep} seconds.')
            time.sleep(sleep)

        if self.args.explain:
            self.connection = InstanceConnection(
                running=True,
                hostname='cloud.example.com',
                port=12345,
                username='root',
                password='password' if self.platform == 'windows' else None,
            )
        else:
            response_json = response.json()
            status = response_json['status']
            con = response_json.get('connection')

            if con:
                self.connection = InstanceConnection(
                    running=status == 'running',
                    hostname=con['hostname'],
                    port=int(con['port']),
                    username=con['username'],
                    password=con.get('password'),
                    response_json=response_json,
                )
            else:
                self.connection = InstanceConnection(
                    running=status == 'running',
                    response_json=response_json,
                )

        if self.connection.password:
            display.sensitive.add(str(self.connection.password))

        status = 'running' if self.connection.running else 'starting'

        display.info(f'The {self.label} instance is {status}.', verbosity=1)

        return self.connection