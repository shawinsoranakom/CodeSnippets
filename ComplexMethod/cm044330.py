def _check_rocm(self) -> None:
        """ Check for ROCm version """
        if self._env.backend != "rocm" or not self._env.system.is_linux:
            logger.debug("Skipping ROCm checks as not enabled")
            return
        rocm = ROCm()

        if rocm.is_valid or rocm.valid_installed:
            self._env.rocm_version = max(rocm.valid_versions)
            logger.info("ROCm version: %s", ".".join(str(v) for v in self._env.rocm_version))
        if rocm.is_valid:
            return
        if rocm.valid_installed:
            str_vers = ".".join(str(v) for v in self._env.rocm_version)
            _InstallState.messages.append(
                f"Valid ROCm version {str_vers} is installed, but is not your default version.\n"
                "You may need to change this to enable GPU acceleration")
            return

        if rocm.versions:
            str_vers = ", ".join(".".join(str(x) for x in v) for v in rocm.versions)
            msg = f"Incompatible ROCm version{'s' if len(rocm.versions) > 1 else ''}: {str_vers}\n"
        else:
            msg = "ROCm not found\n"
            _InstallState.messages.append(f"{msg}\n")
        str_min = ".".join(str(v) for v in rocm.version_min)
        str_max = ".".join(str(v) for v in rocm.version_max)
        valid = f"{str_min} to {str_max}" if str_min != str_max else str_min
        msg += ("The installation can proceed, but you will need to install ROCm version "
                f"{valid} to enable GPU acceleration")
        _InstallState.messages.append(msg)