def _validate_paths(self, full_paths: list[str] | None, is_filter: bool) -> set[str]:
        """Validates that the given image file paths are valid. Exits if paths are provided but no
        images could be found

        Parameters
        ----------
        full_paths
            The list of full paths to images to validate
        is_filter
            ``True`` for filter files. ``False`` for nfilter files

        Returns
        -------
        The list of validated full paths
        """
        if not full_paths:
            return set()
        name = "Filter" if is_filter else ("nFilter")
        retval: list[str] = []
        for file_path in full_paths:

            if os.path.isdir(file_path):
                files = [os.path.join(file_path, fname)
                         for fname in os.listdir(file_path)
                         if os.path.splitext(fname)[-1].lower() in IMAGE_EXTENSIONS]
                if not files:
                    logger.warning("%s folder '%s' contains no image files", name, file_path)
                else:
                    retval.extend(files)
                continue

            if not os.path.splitext(file_path)[-1] in IMAGE_EXTENSIONS:
                logger.warning("%s file '%s' is not an image file. Skipping", name, file_path)
                continue
            if not os.path.isfile(file_path):
                logger.warning("%s file '%s' does not exist. Skipping", name, file_path)
                continue
            retval.append(file_path)

        if not retval:
            logger.error("None of the provided %s files are valid.", name)
            sys.exit(1)

        unique = set(retval)
        logger.debug("[IdentityFilter] %s files: %s", name, unique)
        return unique