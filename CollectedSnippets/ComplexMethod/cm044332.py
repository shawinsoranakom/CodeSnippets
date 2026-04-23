def _from_pip(self,
                  packages: list[dict[T.Literal["name", "package"], str]],
                  extra_args: list[str] | None = None) -> None:
        """ Install packages from pip

        Parameters
        ----------
        packages : list[dict[T.Literal["name", "package"], str]
            The formatted list of packages to be installed
        extra_args : list[str] | None, optional
            Any extra arguments to provide to pip. Default: ``None`` (no extra arguments)
        """
        pipexe = [sys.executable,
                  "-u", "-m", "pip", "install", "--no-cache-dir", "--progress-bar=raw"]

        if not self._env.system.is_admin and not self._env.system.is_virtual_env:
            pipexe.append("--user")  # install as user to solve perm restriction
        if extra_args is not None:
            pipexe.extend(extra_args)
        pipexe.extend([p["package"] for p in packages])
        names = [p["name"] for p in packages]
        installer = Installer(self._env, names, pipexe, False, self._is_gui)
        if installer() != 0:
            msg = f"Unable to install Python packages: {', '.join(names)}"
            logger.warning("%s. Please install these packages manually", msg)
            for line in installer.error_lines:
                _InstallState.messages.append(line)
            _InstallState.failed = True