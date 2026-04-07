def close_rings(self):
        """
        If there are any rings within this geometry that have not been
        closed, this routine will do so by adding the starting point at the
        end.
        """
        # Closing the open rings.
        capi.geom_close_rings(self.ptr)