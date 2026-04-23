def _version_from_lib(self, folder: str) -> tuple[int, int] | None:
        """ Attempt to locate the version from the existence of libcudart.so within a Cuda
        targets/x86_64-linux/lib folder

        Parameters
        ----------
        folder : str
            Full file path to the Cuda folder

        Returns
        -------
        tuple[int, int] | None
            The Cuda version identified by the existence of the libcudart.so file. ``None`` if
            not detected
        """
        lib_folder = os.path.join(folder, "targets", "x86_64-linux", "lib")
        lib_versions = [f.replace(self._lib, "")
                        for f in _files_from_folder(lib_folder, self._lib)]
        if not lib_versions:
            return None
        versions = [self._tuple_from_string(f[1:])
                    for f in lib_versions if f and f.startswith(".")]
        valid = [v for v in versions if v is not None]
        if not valid or not len(set(valid)) == 1:
            return None
        retval = valid[0]
        logger.debug("Version from '%s': %s", os.path.join(lib_folder, self._lib), retval)
        return retval