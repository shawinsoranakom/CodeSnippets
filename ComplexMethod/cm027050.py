def _update_tomato_info(self):
        """Ensure the information from the Tomato router is up to date.

        Return boolean if scanning successful.
        """
        _LOGGER.debug("Scanning")

        try:
            if self.ssl:
                response = requests.Session().send(
                    self.req, timeout=60, verify=self.verify_ssl
                )
            else:
                response = requests.Session().send(self.req, timeout=60)

            # Calling and parsing the Tomato api here. We only need the
            # wldev and dhcpd_lease values.
            if response.status_code == HTTPStatus.OK:
                for param, value in self.parse_api_pattern.findall(response.text):
                    if param in ("wldev", "dhcpd_lease"):
                        self.last_results[param] = json.loads(value.replace("'", '"'))
                return True

            if response.status_code == HTTPStatus.UNAUTHORIZED:
                # Authentication error
                _LOGGER.exception(
                    "Failed to authenticate, please check your username and password"
                )
                return False

        except requests.exceptions.ConnectionError:
            # We get this if we could not connect to the router or
            # an invalid http_id was supplied.
            _LOGGER.exception(
                "Failed to connect to the router or invalid http_id supplied"
            )
            return False

        except requests.exceptions.Timeout:
            # We get this if we could not connect to the router or
            # an invalid http_id was supplied.
            _LOGGER.exception("Connection to the router timed out")
            return False

        except ValueError:
            # If JSON decoder could not parse the response.
            _LOGGER.exception("Failed to parse response from router")
            return False