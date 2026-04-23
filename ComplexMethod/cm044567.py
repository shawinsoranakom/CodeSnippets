def _get_source_dir(self, arguments: Namespace) -> str:
        """Set the correct source folder

        Parameters
        ----------
        arguments
            The command line arguments for the Alignments tool

        Returns
        -------
        Full path to the source folder
        """
        if (hasattr(arguments, "faces_dir") and arguments.faces_dir and
                hasattr(arguments, "frames_dir") and arguments.frames_dir):
            logger.error("Only select a source frames (-fr) or source faces (-fc) folder")
            sys.exit(1)
        elif hasattr(arguments, "faces_dir") and arguments.faces_dir:
            self._type = "faces"
            source_dir = arguments.faces_dir
        elif hasattr(arguments, "frames_dir") and arguments.frames_dir:
            self._type = "frames"
            source_dir = arguments.frames_dir
        else:
            logger.error("No source folder (-fr or -fc) was provided")
            sys.exit(1)
        logger.debug("type: '%s', source_dir: '%s'", self._type, source_dir)
        return source_dir