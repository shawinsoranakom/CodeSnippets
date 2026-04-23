def get_versions(self) -> dict[tuple[int, int], str]:
        """ Attempt to detect all installed Cuda versions on Windows systems from the registry

        Returns
        -------
        dict[tuple[int, int], str]
            The Cuda version to the folder path on Windows
        """
        retval: dict[tuple[int, int], str] = {}
        assert winreg is not None
        reg_key = r"SOFTWARE\NVIDIA Corporation\GPU Computing Toolkit\CUDA"
        paths = {k.lower().replace("cuda_path_", "").replace("_", "."): v
                 for k, v in os.environ.items()
                 if "cuda_path_v" in k.lower()}
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,  # type:ignore[attr-defined]
                                reg_key) as key:
                for version in self._enum_subkeys(key):
                    vers_tuple = self._tuple_from_string(version[1:])
                    if vers_tuple is not None:
                        retval[vers_tuple] = paths.get(version, "")
        except FileNotFoundError:
            logger.debug("Could not find Windows Registry key '%s'", reg_key)
        return {k: retval[k] for k in sorted(retval)}