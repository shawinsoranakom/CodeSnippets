def _update_info(self):
        """Get ARP from router."""
        _LOGGER.debug("Fetching")

        if self._userid is None and not self._login():
            _LOGGER.error("Could not obtain a user ID from the router")
            return False
        last_results = []

        # doing a request
        try:
            res = requests.get(self._url, timeout=10, cookies={"userid": self._userid})
        except requests.exceptions.Timeout:
            _LOGGER.error("Connection to the router timed out at URL %s", self._url)
            return False
        if res.status_code != HTTPStatus.OK:
            _LOGGER.error("Connection failed with http code %s", res.status_code)
            return False
        try:
            result = res.json()
        except ValueError:
            # If json decoder could not parse the response
            _LOGGER.error("Failed to parse response from router")
            return False

        # parsing response
        for info in result:
            mac = info["macAddr"]
            name = info["hostName"]
            # No address = no item :)
            if mac is None:
                continue

            last_results.append(Device(mac.upper(), name))

        self.last_results = last_results

        _LOGGER.debug("Request successful")
        return True