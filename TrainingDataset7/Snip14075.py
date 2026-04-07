def match(self, path):
        # Only use regex overhead if there are converters.
        if self.converters:
            if match := self.regex.search(path):
                # RoutePattern doesn't allow non-named groups so args are
                # ignored.
                kwargs = match.groupdict()
                for key, value in kwargs.items():
                    converter = self.converters[key]
                    try:
                        kwargs[key] = converter.to_python(value)
                    except ValueError:
                        return None
                return path[match.end() :], (), kwargs
        # If this is an endpoint, the path should be exactly the same as the
        # route.
        elif self._is_endpoint:
            if self._route == path:
                return "", (), {}
        # If this isn't an endpoint, the path should start with the route.
        elif path.startswith(route := str(self._route)):
            return path.removeprefix(route), (), {}
        return None