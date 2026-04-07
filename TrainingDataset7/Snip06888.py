def name(self):
        """
        Return description/name string for this driver.
        """
        return force_str(capi.get_driver_description(self.ptr))