def __init__(self, route, name=None, is_endpoint=False):
        self._route = route
        self._regex, self.converters = _route_to_regex(str(route), is_endpoint)
        self._regex_dict = {}
        self._is_endpoint = is_endpoint
        self.name = name