def ensure_registered(cls):
        """
        Attempt to register all the data source drivers.
        """
        # Only register all if the driver count is 0 (or else all drivers will
        # be registered over and over again).
        if not capi.get_driver_count():
            capi.register_all()