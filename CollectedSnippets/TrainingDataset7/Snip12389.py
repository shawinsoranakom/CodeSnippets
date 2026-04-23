def __init__(self, routers=None):
        """
        If routers is not specified, default to settings.DATABASE_ROUTERS.
        """
        self._routers = routers