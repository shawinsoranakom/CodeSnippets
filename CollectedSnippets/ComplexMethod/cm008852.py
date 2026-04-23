def load_configs(self):
        directory = ''
        if self.filename:
            location = os.path.realpath(self.filename)
            directory = os.path.dirname(location)
            if location in self._loaded_paths:
                return False
            self._loaded_paths.add(location)

        self.__initialized = True
        opts, _ = self.parser.parse_known_args(self.own_args)
        self.parsed_args = self.own_args
        for location in opts.config_locations or []:
            if location == '-':
                if location in self._loaded_paths:
                    continue
                self._loaded_paths.add(location)
                self.append_config(shlex.split(read_stdin('options'), comments=True), label='stdin')
                continue
            location = os.path.join(directory, expand_path(location))
            if os.path.isdir(location):
                location = os.path.join(location, 'yt-dlp.conf')
            if not os.path.exists(location):
                self.parser.error(f'config location {location} does not exist')
            self.append_config(self.read_file(location), location)
        return True