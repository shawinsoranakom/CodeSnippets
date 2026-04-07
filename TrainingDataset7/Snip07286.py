def valid_reason(self):
        """
        Return a string containing the reason for any invalidity.
        """
        return capi.geos_isvalidreason(self.ptr).decode()