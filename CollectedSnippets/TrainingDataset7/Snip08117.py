def find(self, path, find_all=False):
        """
        Look for files in the app directories.
        """
        matches = []
        for app in self.apps:
            app_location = self.storages[app].location
            if app_location not in searched_locations:
                searched_locations.append(app_location)
            match = self.find_in_app(app, path)
            if match:
                if not find_all:
                    return match
                matches.append(match)
        return matches