def vsi_buffer(self):
        if not (
            self.is_vsi_based and self.name.startswith(VSI_MEM_FILESYSTEM_BASE_PATH)
        ):
            return None
        # Prepare an integer that will contain the buffer length.
        out_length = c_int()
        # Get the data using the vsi file name.
        dat = capi.get_mem_buffer_from_vsi_file(
            force_bytes(self.name),
            byref(out_length),
            VSI_DELETE_BUFFER_ON_READ,
        )
        # Read the full buffer pointer.
        return string_at(dat, out_length.value)