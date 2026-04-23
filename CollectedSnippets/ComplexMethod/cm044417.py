def _set_folder_filename(self,
                             location: str | None,
                             source_location: str,
                             input_is_video: bool) -> tuple[str, str, bool]:
        """Return the folder and the filename for the alignments file.

        If the location is not provided then for videos, the alignments file will be stored in the
        same folder as the video, with filename `<video_name>_alignments`. For a folder of images,
        the alignments file will be stored in folder with the images and just be called
        'alignments'

        Parameters
        ----------
        location
            Full path to the alignments file. ``None`` to derive from the source file location
        source_location
            Full path to the source media for the alignments file. Either a folder of images or a
            video file
        input_is_video:
            ``True`` if the input to the process is a video, ``False`` if it is a folder of images.

        Returns
        -------
        folder
            The folder where the alignments file will be stored
        filename
            The filename of the alignments file
        needs_import
            ``True`` if a 'file' plugin is being used for detect/align and the provided file is a
            .json file
        """
        if location:
            logger.debug("Alignments File provided: '%s'", location)
            folder, filename = os.path.split(str(location))
            if not self._plugin_is_file and os.path.splitext(filename)[-1].lower() == ".json":
                logger.error("Json files are only valid with 'File' detect/align plugins.")
                sys.exit(1)
        elif input_is_video:
            logger.debug("Alignments from Video File: '%s'", source_location)
            folder, filename = os.path.split(source_location)
            filename = f"{os.path.splitext(filename)[0]}_alignments"
        else:
            logger.debug("Alignments from Input Folder: '%s'", source_location)
            folder = str(source_location)
            filename = "alignments"
        logger.debug("Setting Alignments: (folder: '%s' filename: '%s')", folder, filename)

        if not self._plugin_is_file:
            return folder, filename, False

        full_path = os.path.join(folder, filename)
        for ext in (".json", ".fsa"):
            if os.path.splitext(filename)[-1].lower() in ext and os.path.exists(full_path):
                return folder, os.path.splitext(filename)[0], ext == ".json"
            full_file = f"{full_path}{ext}"
            if os.path.exists(full_file):
                return folder, filename, ext == ".json"

        logger.error("'File' has been selected for a Detect or Align plugin, but no alignments "
                     "file could be found. Check your paths.")
        sys.exit(1)