def update_device(self) -> bool:
        """Get the latest details from the device."""
        try:
            telnet = telnetlib.Telnet(self._host, self._port, self._timeout)
        except OSError:
            _LOGGER.warning("Pioneer %s refused connection", self._name)
            return False

        pwstate = self.telnet_request(telnet, "?P", "PWR")
        if pwstate:
            self._pwstate = pwstate

        volume_str = self.telnet_request(telnet, "?V", "VOL")
        self._volume = int(volume_str[3:]) / MAX_VOLUME if volume_str else None

        muted_value = self.telnet_request(telnet, "?M", "MUT")
        self._muted = (muted_value == "MUT0") if muted_value else None

        # Build the source name dictionaries if necessary
        if not self._source_name_to_number:
            for i in range(MAX_SOURCE_NUMBERS):
                result = self.telnet_request(telnet, f"?RGB{str(i).zfill(2)}", "RGB")

                if not result:
                    continue

                source_name = result[6:]
                source_number = str(i).zfill(2)

                self._source_name_to_number[source_name] = source_number
                self._source_number_to_name[source_number] = source_name

        source_number = self.telnet_request(telnet, "?F", "FN")

        if source_number:
            self._selected_source = self._source_number_to_name.get(source_number[2:])
        else:
            self._selected_source = None

        telnet.close()
        return True