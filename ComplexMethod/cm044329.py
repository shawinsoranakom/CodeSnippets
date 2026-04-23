def _check_cuda(self) -> None:
        """ Check for Cuda and cuDNN Locations. """
        if self._env.backend != "nvidia":
            logger.debug("Skipping Cuda checks as not enabled")
            return
        if not any((self._env.system.is_linux, self._env.system.is_windows)):
            return
        cuda = Cuda()
        if cuda.versions:
            str_vers = ", ".join(".".join(str(x) for x in v) for v in cuda.versions)
            msg = (f"Globally installed Cuda version{'s' if len(cuda.versions) > 1 else ''} "
                   f"{str_vers} found. PyTorch uses it's own version of Cuda, so if you have "
                   "GPU issues, you should remove these global installs")
            _InstallState.messages.append(msg)
            self._env.cuda_cudnn[0] = str_vers
            logger.debug("CUDA version: %s", self._env.cuda_version)
        if cuda.cudnn_versions:
            str_vers = ", ".join(".".join(str(x) for x in v)
                                 for v in cuda.cudnn_versions.values())
            msg = ("Globally installed CuDNN version"
                   f"{'s' if len(cuda.cudnn_versions) > 1 else ''} {str_vers} found. PyTorch uses "
                   "its own version of Cuda, so if you have GPU issues, you should remove these "
                   "global installs")
            _InstallState.messages.append(msg)
            self._env.cuda_cudnn[1] = str_vers
            logger.debug("cuDNN version: %s", self._env.cudnn_version)