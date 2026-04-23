def load_from_file(self, file_name: str, cache: str = 'all', unsafe: bool = False, json_only: bool = False, trusted_as_template: bool = False) -> t.Any:
        """
        Loads data from a file, which can contain either JSON or YAML.

        :param file_name: The name of the file to load data from.
        :param cache: Options for caching: none|all|vaulted
        :param unsafe: If True, returns the parsed data as-is without deep copying.
        :param json_only: If True, only loads JSON data from the file.
        :return: The loaded data, optionally deep-copied for safety.
        """

        # Resolve the file name
        file_name = self.path_dwim(file_name)

        # Log the file being loaded
        display.debug("Loading data from %s" % file_name)

        # Check if the file has been cached and use the cached data if available
        if cache != 'none' and file_name in self._FILE_CACHE:
            parsed_data = self._FILE_CACHE[file_name]
        else:
            file_data = self.get_text_file_contents(file_name)

            if trusted_as_template:
                file_data = TrustedAsTemplate().tag(file_data)

            parsed_data = self.load(data=file_data, file_name=file_name, json_only=json_only)

            # only tagging the container, used by include_vars to determine if vars should be shown or not
            # this is a temporary measure until a proper data senitivity system is in place
            if SourceWasEncrypted.is_tagged_on(file_data):
                parsed_data = SourceWasEncrypted().tag(parsed_data)

            # Cache the file contents for next time based on the cache option
            if cache == 'all':
                self._FILE_CACHE[file_name] = parsed_data
            elif cache == 'vaulted' and SourceWasEncrypted.is_tagged_on(file_data):
                self._FILE_CACHE[file_name] = parsed_data

        # Return the parsed data, optionally deep-copied for safety
        if unsafe:
            return parsed_data
        else:
            return copy.deepcopy(parsed_data)