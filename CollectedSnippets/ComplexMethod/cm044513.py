def load(self, *args,  # pylint:disable=unused-argument
             filename=None, current_tab=True):
        """ Load a task into this :class:`Tasks` class.

        Tasks can be loaded from project ``.fsw`` files or task ``.fst`` files, depending on where
        this function is being called from.

        Parameters
        ----------
        *args: tuple
            Unused, but needs to be present for arguments passed by tkinter event handling
        filename: str, optional
            If a filename is passed in, This will be used, otherwise a file handler will be
            launched to select the relevant file.
        current_tab: bool, optional
            ``True`` if the task to be loaded must be for the currently selected tab. ``False``
            if loading a task into any tab. If current_tab is `True` then tasks can be loaded from
            ``.fsw`` and ``.fst`` files, otherwise they can only be loaded from ``.fst`` files.
            Default: ``True``
        """
        logger.debug("Loading task config: (filename: '%s', current_tab: '%s')",
                     filename, current_tab)

        # Option to load specific task from project files:
        sess_type = "all" if current_tab else "task"

        is_legacy = (not self._is_project and
                     filename is not None and sess_type == "task" and
                     os.path.splitext(filename)[1] == ".fsw")
        if is_legacy:
            logger.debug("Legacy task found: '%s'", filename)
            filename = self._update_legacy_task(filename)

        filename_set = self._set_filename(filename, sess_type=sess_type)
        if not filename_set:
            return
        loaded = self._load()
        if not loaded:
            return

        command = self._active_tab if current_tab else self._stored_tab_name
        command = self._get_lone_task() if command is None else command
        if command is None:
            logger.error("Unable to determine task from the given file: '%s'", filename)
            return
        if command not in self._options:
            logger.error("No '%s' task in '%s'", command, self._filename)
            return

        self._set_options(command)
        self._add_to_recent(command)

        if self._is_project:
            self._filename = self._project_filename
        elif self._filename.endswith(".fsw"):
            self._filename = None

        self._add_task(command)
        if is_legacy:
            self.save()

        logger.debug("Loaded task config: (command: '%s', filename: '%s')", command, filename)