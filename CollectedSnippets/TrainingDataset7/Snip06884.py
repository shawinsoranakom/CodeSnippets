def __init__(self, dr_input):
        """
        Initialize an GDAL/OGR driver on either a string or integer input.
        """
        if isinstance(dr_input, str):
            # If a string name of the driver was passed in
            self.ensure_registered()

            # Checking the alias dictionary (case-insensitive) to see if an
            # alias exists for the given driver.
            if dr_input.lower() in self._alias:
                name = self._alias[dr_input.lower()]
            else:
                name = dr_input

            # Attempting to get the GDAL/OGR driver by the string name.
            driver = c_void_p(capi.get_driver_by_name(force_bytes(name)))
        elif isinstance(dr_input, int):
            self.ensure_registered()
            driver = capi.get_driver(dr_input)
        elif isinstance(dr_input, c_void_p):
            driver = dr_input
        else:
            raise GDALException(
                "Unrecognized input type for GDAL/OGR Driver: %s" % type(dr_input)
            )

        # Making sure we get a valid pointer to the OGR Driver
        if not driver:
            raise GDALException(
                "Could not initialize GDAL/OGR Driver on input: %s" % dr_input
            )
        self.ptr = driver