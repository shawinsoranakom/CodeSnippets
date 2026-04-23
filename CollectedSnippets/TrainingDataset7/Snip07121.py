def __del__(self):
        if self.is_vsi_based:
            # Remove the temporary file from the VSI in-memory filesystem.
            capi.unlink_vsi_file(force_bytes(self.name))
        super().__del__()