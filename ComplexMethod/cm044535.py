def _set_kwargs(self,
                    title: str | None,
                    initial_folder: str | None,
                    initial_file: str | None,
                    file_type: _FILETYPE | None,
                    command: str | None,
                    action: str | None,
                    variable: str | None,
                    parent: tk.Frame | ttk.Frame | None
                    ) -> dict[str, None | tk.Frame | ttk.Frame | str | list[tuple[str, str]]]:
        """ Generate the required kwargs for the requested file dialog browser.

        Parameters
        ----------
        title: str
            The title to display on the file dialog. If `None` then the default title will be used.
        initial_folder: str
            The folder to initially open with the file dialog. If `None` then tkinter will decide.
        initial_file: str
            The filename to set with the file dialog. If `None` then tkinter no initial filename
            is.
        file_type: ['default', 'alignments', 'config_project', 'config_task', 'config_all', \
                    'csv',  'image', 'ini', 'state', 'log', 'video'] or ``None``
            The type of file that this dialog is for. `default` allows selection of any files.
            Other options limit the file type selection
        command: str
            Required for context handling file dialog, otherwise unused.
        action: str
            Required for context handling file dialog, otherwise unused.
        variable: str, optional
            Required for context handling file dialog, otherwise unused. The variable to associate
            with this file dialog. Default: ``None``
        parent: :class:`tkinter.Frame` | :class:`tkinter.tk.Frame | None
            The parent that is launching the file dialog. ``None`` sets this to root

        Returns
        -------
        dict:
            The key word arguments for the file dialog to be launched
        """
        logger.debug("Setting Kwargs: (title: %s, initial_folder: %s, initial_file: '%s', "
                     "file_type: '%s', command: '%s': action: '%s', variable: '%s', parent: %s)",
                     title, initial_folder, initial_file, file_type, command, action, variable,
                     parent)

        kwargs: dict[str, None | tk.Frame | ttk.Frame | str | list[tuple[str, str]]] = {
            "master": self._dummy_master}

        if self._handletype.lower() == "context":
            assert command is not None and action is not None and variable is not None
            self._set_context_handletype(command, action, variable)

        if title is not None:
            kwargs["title"] = title

        if initial_folder is not None:
            kwargs["initialdir"] = initial_folder

        if initial_file is not None:
            kwargs["initialfile"] = initial_file

        if parent is not None:
            kwargs["parent"] = parent

        if self._handletype.lower() in (
                "open", "save", "filename", "filename_multi", "save_filename"):
            assert file_type is not None
            kwargs["filetypes"] = self._filetypes[file_type]
            if self._defaults.get(file_type):
                kwargs['defaultextension'] = self._defaults[file_type]
        if self._handletype.lower() == "save":
            kwargs["mode"] = "w"
        if self._handletype.lower() == "open":
            kwargs["mode"] = "r"
        logger.debug("Set Kwargs: %s", kwargs)
        return kwargs