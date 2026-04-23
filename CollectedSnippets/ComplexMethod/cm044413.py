def _validate_compatible_args(cls, args: Namespace) -> Namespace:
        """Some cli arguments are not compatible with each other. If conflicting arguments have
        been selected, log a warning and make necessary changes

        Parameters
        ----------
        args
            The command line arguments to be checked and updated for conflicts

        Returns
        -------
        The updated command line arguments
        """
        # Can't run a detector if importing landmarks
        if args.aligner == "file" and args.detector != "file":
            logger.warning("Detecting faces is not compatible with importing landmarks from a "
                           "file. Setting Detector to 'file'")
            args.detector = "file"
        # Impossible to skip existing when not running detection
        if args.skip_existing and args.detector == "file":
            logger.warning("Skipping existing frames is not compatible with importing from a file "
                           "for detection. Disabling 'skip_existing'")
            args.skip_existing = False
        # Impossible to get missing faces when we do not have a detector or aligner
        if args.skip_faces and (args.detector == "file" or args.aligner == "file"):
            logger.warning("Skipping existing faces is not compatible with importing from a file. "
                           "Disabling 'skip_existing_faces'")
            args.skip_faces = False
        # Face filtering needs a recognition plugin
        if (args.filter or args.nfilter) and not args.identity:
            logger.warning("Face-filtering is enabled, but an identity plugin has not been "
                           "selected. Selecting 'T-Face' plugin")
            args.identity = ["t-face"]
        # We can only use 1 identity for face filtering, so we select the first given
        if (args.filter or args.nfilter) and len(args.identity) > 1:
            logger.warning("Face-filtering is enabled, but multiple identity plugins have been "
                           "selected. Using '%s' for filtering", args.identity[0])
        return args