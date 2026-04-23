def __init__(self, regex, name=None, is_endpoint=False):
        self._regex = regex
        self._regex_dict = {}
        self._is_endpoint = is_endpoint
        self.name = name
        self.converters = {}