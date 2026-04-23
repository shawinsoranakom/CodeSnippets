def _load(self) -> dict[str, T.Any]:
        """Override the parent :func:`~lib.align.Alignments._load` to handle skip existing
        frames and faces on extract.

        If skip existing has been selected, existing alignments are loaded and returned to the
        calling script.

        Returns
        -------
        Any alignments that have already been extracted if skip existing has been selected
        otherwise an empty dictionary
        """
        data: dict[str, T.Any] = {}
        if not self._is_extract and not self.have_alignments_file:
            return data
        if not self._is_extract:
            data = super()._load()
            return data

        if (not self._skip_existing_frames
                and not self._skip_existing_faces
                and not self._plugin_is_file):
            logger.debug("No previous alignments file required. Returning empty dictionary")
            return data

        file_exists = self.have_alignments_file or self._import_json

        if not file_exists and (self._skip_existing_frames or self._skip_existing_faces):
            logger.warning("Skip Existing/Skip Faces selected, but no alignments file found!")
        if not file_exists:
            return data

        if self._import_json and self.have_alignments_file:
            logger.warning("Importing alignments from json, but alignments file exists: '%s'",
                           self._io.file)
            self.backup()
        if self._import_json:
            return data

        data = super()._load()
        return data