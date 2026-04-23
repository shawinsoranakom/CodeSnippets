def _get_missing_conda(self) -> dict[str, list[dict[T.Literal["name", "package"], str]]]:
        """ Check for conda missing dependencies

        Returns
        -------
        dict[str, list[dict[Literal["name", "package"], str]]]
            The Conda packages to install grouped by channel
        """
        retval: dict[str, list[dict[T.Literal["name", "package"], str]]] = {}
        if not self._env.system.is_conda:
            return retval
        required = self._get_required_conda()
        requirements = self._requirements.parse_requirements(
            [p["package"] for p in required])
        channels = [p["channel"] for p in required]
        installed = {k: v for k, v in self._packages.installed_conda.items() if v[1] != "pypi"}
        for req, channel in zip(requirements, channels):
            spec_str = str(req.specifier).replace("==", "=") if req.specifier else ""
            package: dict[T.Literal["name", "package"], str] = {"name": req.name.title(),
                                                                "package": f"{req.name}{spec_str}"}
            exists = installed.get(req.name)
            if req.name == "tk" and self._env.system.is_linux:
                # Default TK has bad fonts under Linux.
                # Ref: https://github.com/ContinuumIO/anaconda-issues/issues/6833
                # This versioning will fail in parse_requirements, so we need to do it here
                package["package"] = f"{req.name}=*=xft_*"  # Swap out for explicit XFT version
                if exists is not None and not exists[1].startswith("xft"):  # Replace noxft version
                    exists = None
            if not exists:
                logger.debug("Adding new Conda package '%s'", package["package"])
                retval.setdefault(channel, []).append(package)
                continue
            if exists[-1] != channel:
                logger.debug("Adding Conda package '%s' for channel change from '%s' to '%s'",
                             package["package"], exists[-1], channel)
                retval.setdefault(channel, []).append(package)
                continue
            if not req.specifier.contains(exists[0]):
                logger.debug("Adding Conda package '%s' for specifier change from '%s' to '%s'",
                             package["package"], exists[0], spec_str)
                retval.setdefault(channel, []).append(package)
                continue
            logger.debug("Skipping installed Conda package '%s'", package["package"])
        logger.debug("Selected missing Conda packages: %s", retval)
        return retval