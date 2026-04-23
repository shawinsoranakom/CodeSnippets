def _build_recent_menu(self) -> None:
        """ Load recent files into menu bar """
        logger.debug("Building Recent Files menu")
        serializer = get_serializer("json")
        menu_file = os.path.join(self._config.pathcache, ".recent.json")
        recent_files = []
        if not os.path.isfile(menu_file) or os.path.getsize(menu_file) == 0:
            self._clear_recent_files(serializer, menu_file)
        try:
            recent_files = serializer.load(menu_file)
        except FaceswapError as err:
            if "Error unserializing data for type" in str(err):
                # Some reports of corruption breaking menus
                logger.warning("There was an error opening the recent files list so it has been "
                               "reset.")
                self._clear_recent_files(serializer, menu_file)

        logger.debug("Loaded recent files: %s", recent_files)
        removed_files = []
        for recent_item in recent_files:
            filename, command = recent_item
            if not os.path.isfile(filename):
                logger.debug("File does not exist. Flagging for removal: '%s'", filename)
                removed_files.append(recent_item)
                continue
            # Legacy project files didn't have a command stored
            command = command if command else "project"
            logger.debug("processing: ('%s', %s)", filename, command)
            if command.lower() == "project":
                load_func = self._config.project.load
                lbl = command
                kwargs = {"filename": filename}
            else:
                load_func = self._config.tasks.load  # type:ignore
                lbl = _("{} Task").format(command)
                kwargs = {"filename": filename, "current_tab": False}
            self.recent_menu.add_command(
                label=f"{filename} ({lbl.title()})",
                command=lambda kw=kwargs, fn=load_func: fn(**kw))  # type:ignore
        if removed_files:
            for recent_item in removed_files:
                logger.debug("Removing from recent files: `%s`", recent_item[0])
                recent_files.remove(recent_item)
            serializer.save(menu_file, recent_files)
        self.recent_menu.add_separator()
        self.recent_menu.add_command(
            label=_("Clear recent files"),
            underline=0,
            command=lambda srl=serializer, mnu=menu_file: self._clear_recent_files(  # type:ignore
                srl, mnu))

        logger.debug("Built Recent Files menu")