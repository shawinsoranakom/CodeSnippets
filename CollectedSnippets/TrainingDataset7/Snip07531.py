def __init__(self, locations=None):
        # If no locations specified, then we try to build for
        # every model in installed applications.
        self.locations = self._build_kml_sources(locations)