def _get_sysbrowser(self,
                        option: dict[str, T.Any],
                        options: list[dict[str, T.Any]],
                        command: str) -> dict[T.Literal["filetypes",
                                                        "browser",
                                                        "command",
                                                        "destination",
                                                        "action_option"], str | list[str]] | None:
        """ Return the system file browser and file types if required

        Parameters
        ----------
        option: dict[str, Any]
            The option to obtain the system browser for
        options: list[dict[str, Any]]
            The full list of options for the command
        command: str
            The command that the options belong to

        Returns
        -------
        dict[Literal["filetypes", "browser", "command",
                     "destination", "action_option"], list[str]] | None
            The browser information, if valid, or ``None`` if browser not required
        """
        action = option.get("action", None)
        if action not in (actions.DirFullPaths,
                          actions.FileFullPaths,
                          actions.FilesFullPaths,
                          actions.DirOrFileFullPaths,
                          actions.DirOrFilesFullPaths,
                          actions.SaveFileFullPaths,
                          actions.ContextFullPaths):
            return None

        retval: dict[T.Literal["filetypes",
                               "browser",
                               "command",
                               "destination",
                               "action_option"], str | list[str]] = {}
        action_option = None
        if option.get("action_option", None) is not None:
            self._expand_action_option(option, options)
            action_option = option["action_option"]
        retval["filetypes"] = option.get("filetypes", "default")
        if action == actions.FileFullPaths:
            retval["browser"] = ["load"]
        elif action == actions.FilesFullPaths:
            retval["browser"] = ["multi_load"]
        elif action == actions.SaveFileFullPaths:
            retval["browser"] = ["save"]
        elif action == actions.DirOrFileFullPaths:
            retval["browser"] = ["folder", "load"]
        elif action == actions.DirOrFilesFullPaths:
            retval["browser"] = ["folder", "multi_load"]
        elif action == actions.ContextFullPaths and action_option:
            retval["browser"] = ["context"]
            retval["command"] = command
            retval["action_option"] = action_option
            retval["destination"] = option.get("dest", option["opts"][1].replace("--", ""))
        else:
            retval["browser"] = ["folder"]
        logger.debug(retval)
        return retval