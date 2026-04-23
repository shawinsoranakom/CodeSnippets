def __init__(self, nodelist, origin, name, source_start=None, source_end=None):
        self.nodelist = nodelist
        self.origin = origin
        self.name = name
        # If available (debug mode), the absolute character offsets in the
        # template.source correspond to the full partial region.
        self._source_start = source_start
        self._source_end = source_end