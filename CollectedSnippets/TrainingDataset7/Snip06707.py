def __init__(self, *args, **kwargs):
        # Trying to find the location of the SpatiaLite library.
        # Here we are figuring out the path to the SpatiaLite library
        # (`libspatialite`). If it's not in the system library path (e.g., it
        # cannot be found by `ctypes.util.find_library`), then it may be set
        # manually in the settings via the `SPATIALITE_LIBRARY_PATH` setting.
        self.lib_spatialite_paths = [
            name
            for name in [
                getattr(settings, "SPATIALITE_LIBRARY_PATH", None),
                "mod_spatialite.so",
                "mod_spatialite",
                find_library("spatialite"),
            ]
            if name is not None
        ]
        super().__init__(*args, **kwargs)