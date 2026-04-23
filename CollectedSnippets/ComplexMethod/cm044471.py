def _configure_backend(self, arguments: argparse.Namespace) -> None:
        """Configure the backend.

        Exclude any GPUs for use by Faceswap when requested.

        Set Faceswap backend to CPU if all GPUs have been deselected.

        Parameters
        ----------
        arguments
            The command line arguments passed to Faceswap.
        """
        if not hasattr(arguments, "exclude_gpus"):
            # CPU backends and systems where no GPU was detected will not have this attribute
            logger.debug("Adding missing exclude gpus argument to namespace")
            setattr(arguments, "exclude_gpus", None)
            return

        assert GPUStats is not None
        if arguments.exclude_gpus:
            if not all(idx.isdigit() for idx in arguments.exclude_gpus):
                logger.error("GPUs passed to the ['-X', '--exclude-gpus'] argument must all be "
                             "integers.")
                sys.exit(1)
            arguments.exclude_gpus = [int(idx) for idx in arguments.exclude_gpus]
            GPUStats().exclude_devices(arguments.exclude_gpus)

        if GPUStats().exclude_all_devices:
            msg = "Switching backend to CPU"
            set_backend("cpu")
            logger.info(msg)

        logger.debug("Executing: %s. PID: %s", self._command, os.getpid())