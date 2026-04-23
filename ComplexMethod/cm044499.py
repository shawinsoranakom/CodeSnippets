def _populate_from_folder(self, *args):  # pylint:disable=unused-argument
        """ Populate the Analysis tab from a model folder.

        Triggered when :attr:`vars` ``analysis_folder`` variable is is set.
        """
        if Session.is_training:
            return

        folder = self.vars["analysis_folder"].get()
        if not folder or not os.path.isdir(folder):
            logger.debug("Not a valid folder")
            self._clear_session()
            return

        state_files = [fname
                       for fname in os.listdir(folder)
                       if fname.endswith("_state.json")]
        if not state_files:
            logger.debug("No state files found in folder: '%s'", folder)
            self._clear_session()
            return

        state_file = state_files[0]
        if len(state_files) > 1:
            logger.debug("Multiple models found. Selecting: '%s'", state_file)

        if self._thread is None:
            self._load_session(full_path=os.path.join(folder, state_file))