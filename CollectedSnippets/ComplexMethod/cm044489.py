def _get_cudnn_paths(self) -> list[str]:  # noqa[C901]
        """ Attempt to locate the locations of cuDNN installs for Windows

        Returns
        -------
        list[str]
            Full path to existing cuDNN installs under Windows
        """
        assert winreg is not None
        paths: set[str] = set()
        cudnn_key = "cudnn_cuda"
        reg_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        lookups = (winreg.HKEY_LOCAL_MACHINE,  # type:ignore[attr-defined]
                   winreg.HKEY_CURRENT_USER)  # type:ignore[attr-defined]
        for lookup in lookups:
            try:
                key = winreg.OpenKey(lookup, reg_key)  # type:ignore[attr-defined]
            except FileNotFoundError:
                continue
            for name in self._enum_subkeys(key):
                if cudnn_key not in name.lower():
                    logger.debug("Skipping subkey '%s'", name)
                    continue
                try:
                    subkey = winreg.OpenKey(key, name)  # type:ignore[attr-defined]
                    logger.debug("Skipping subkey not found '%s'", name)
                except FileNotFoundError:
                    continue
                logger.debug("Parsing cudnn key '%s'", cudnn_key)
                try:
                    path, _ = winreg.QueryValueEx(subkey,  # type:ignore[attr-defined]
                                                  "InstallLocation")
                except (FileNotFoundError, OSError):
                    logger.debug("Skipping missing InstallLocation for sub-key '%s'", subkey)
                    continue
                if not os.path.isdir(path):
                    logger.debug("Skipping non-existant path '%s'", path)
                    continue
                paths.add(path)
        retval = list(paths)
        logger.debug("cudnn install paths: %s", retval)
        return retval