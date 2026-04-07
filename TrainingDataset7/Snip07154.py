def identify_epsg(self):
        """
        This method inspects the WKT of this SpatialReference, and will
        add EPSG authority nodes where an EPSG identifier is applicable.
        """
        capi.identify_epsg(self.ptr)