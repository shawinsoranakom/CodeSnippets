def _get_backend(self) -> ValidBackends:
        """Return the backend from either the `FACESWAP_BACKEND` Environment Variable or from
        the :file:`config/.faceswap` configuration file. If neither of these exist, prompt the user
        to select a backend.

        Returns
        -------
        The backend configuration in use by Faceswap
        """
        # Check if environment variable is set, if so use that
        if "FACESWAP_BACKEND" in os.environ:
            fs_backend = T.cast(ValidBackends, os.environ["FACESWAP_BACKEND"].lower())
            assert fs_backend in T.get_args(ValidBackends), (
                f"Faceswap backend must be one of {T.get_args(ValidBackends)}")
            print(f"Setting Faceswap backend from environment variable to {fs_backend.upper()}")
            return fs_backend
        # Intercept for sphinx docs build
        if sys.argv[0].endswith("sphinx-build"):
            return "nvidia"
        if not os.path.isfile(self._config_file):
            self._configure_backend()
        while True:
            try:
                with open(self._config_file, "r", encoding="utf8") as cnf:
                    config = json.load(cnf)
                break
            except json.decoder.JSONDecodeError:
                self._configure_backend()
                continue
        fs_backend = config.get("backend", "").lower()
        if not fs_backend or fs_backend not in self._backends.values():
            fs_backend = self._configure_backend()
        if current_process().name == "MainProcess":
            print(f"Setting Faceswap backend to {fs_backend.upper()}")
        return fs_backend