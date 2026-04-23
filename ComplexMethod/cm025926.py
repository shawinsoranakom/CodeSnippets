def _build_options(self):
        """Build the command line and strip out last results that do not need to be updated."""
        options = self._options
        if self.home_interval:
            boundary = dt_util.now() - self.home_interval
            last_results = [
                device for device in self._last_results if device.last_update > boundary
            ]
            if last_results:
                exclude_hosts = self._exclude + [device.ipv4 for device in last_results]
            else:
                exclude_hosts = self._exclude
        else:
            last_results = []
            exclude_hosts = self._exclude
        if exclude_hosts:
            options += f" --exclude {','.join(exclude_hosts)}"
        # Report reason
        if "--reason" not in options:
            options += " --reason"
        # Report down hosts
        if "-v" not in options:
            options += " -v"
        self._last_results = last_results
        return options