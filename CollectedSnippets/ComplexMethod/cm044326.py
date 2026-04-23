def _parse_backend_from_cli(self, arg: str) -> None:
        """ Parse a command line argument and populate :attr:`backend` if valid

        Parameters
        ----------
        arg : str
            The command line argument to parse
        """
        arg = arg.lower()
        if not any(arg.startswith(b) for b in self._backends):
            return
        self.set_backend(next(b for b in self._backends if arg.startswith(b)))  # type:ignore[misc]
        if arg == "cpu":
            self.set_requirements("cpu")
            return
        # Get Cuda/ROCm requirements file
        assert self.backend is not None
        req_files = sorted([os.path.splitext(f)[0].replace("requirements_", "")
                            for f in os.listdir(os.path.join(PROJECT_ROOT, "requirements"))
                            if os.path.splitext(f)[-1] == ".txt"
                            and f.startswith("requirements_")
                            and self.backend in f])
        if arg == self.backend:  # Default to latest
            logger.debug("No version specified. Defaulting to latest requirements")
            self.set_requirements(req_files[-1])
            return
        lookup = [r.replace("_", "") for r in req_files]
        if arg not in lookup:
            logger.debug("Defaulting to latest requirements for unknown lookup '%s'", arg)
            self.set_requirements(req_files[-1])
            return
        self.set_requirements(req_files[lookup.index(arg)])