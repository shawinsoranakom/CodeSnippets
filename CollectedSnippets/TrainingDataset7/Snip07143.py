def clone(self, name=None):
        """Return a clone of this GDALRaster."""
        if name:
            clone_name = name
        elif self.driver.name != "MEM":
            clone_name = self.name + "_copy." + self.driver.name
        else:
            clone_name = os.path.join(VSI_MEM_FILESYSTEM_BASE_PATH, str(uuid.uuid4()))
        return GDALRaster(
            capi.copy_ds(
                self.driver._ptr,
                force_bytes(clone_name),
                self._ptr,
                c_int(),
                c_char_p(),
                c_void_p(),
                c_void_p(),
            ),
            write=self._write,
        )