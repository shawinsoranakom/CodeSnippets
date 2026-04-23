def do_update(self) -> bool:
        """Get the latest details from the device, as boolean."""
        try:
            telnet = telnetlib.Telnet(self._host)
        except OSError:
            return False

        if self._should_setup_sources:
            self._setup_sources(telnet)
            self._should_setup_sources = False

        self._pwstate = self.telnet_request(telnet, "PW?")
        for line in self.telnet_request(telnet, "MV?", all_lines=True):
            if line.startswith("MVMAX "):
                # only grab two digit max, don't care about any half digit
                self._volume_max = int(line[len("MVMAX ") : len("MVMAX XX")])
                continue
            if line.startswith("MV"):
                self._volume = int(line.removeprefix("MV"))
        self._muted = self.telnet_request(telnet, "MU?") == "MUON"
        self._mediasource = self.telnet_request(telnet, "SI?").removeprefix("SI")

        if self._mediasource in MEDIA_MODES.values():
            self._mediainfo = ""
            answer_codes = [
                "NSE0",
                "NSE1X",
                "NSE2X",
                "NSE3X",
                "NSE4",
                "NSE5",
                "NSE6",
                "NSE7",
                "NSE8",
            ]
            for line in self.telnet_request(telnet, "NSE", all_lines=True):
                self._mediainfo += f"{line.removeprefix(answer_codes.pop(0))}\n"
        else:
            self._mediainfo = self.source

        telnet.close()
        return True