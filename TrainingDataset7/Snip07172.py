def import_proj(self, proj):
        """Import the Spatial Reference from a PROJ string."""
        capi.from_proj(self.ptr, proj)