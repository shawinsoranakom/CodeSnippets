def is_vsi_based(self):
        return self._ptr and self.name.startswith(VSI_FILESYSTEM_PREFIX)