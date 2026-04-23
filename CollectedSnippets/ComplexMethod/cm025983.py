def _setup_sources(self, telnet):
        # NSFRN - Network name
        nsfrn = self.telnet_request(telnet, "NSFRN ?").removeprefix("NSFRN ")
        if nsfrn:
            self._name = nsfrn

        # SSFUN - Configured sources with (optional) names
        self._source_list = {}
        for line in self.telnet_request(telnet, "SSFUN ?", all_lines=True):
            ssfun = line.removeprefix("SSFUN").split(" ", 1)

            source = ssfun[0]
            if len(ssfun) == 2 and ssfun[1]:
                configured_name = ssfun[1]
            else:
                # No name configured, reusing the source name
                configured_name = source

            self._source_list[configured_name] = source

        # SSSOD - Deleted sources
        for line in self.telnet_request(telnet, "SSSOD ?", all_lines=True):
            source, status = line.removeprefix("SSSOD").split(" ", 1)
            if status == "DEL":
                for pretty_name, name in self._source_list.items():
                    if source == name:
                        del self._source_list[pretty_name]
                        break