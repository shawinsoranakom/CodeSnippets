def _set_help(cls, btntype: str) -> str:
        """ Set the helptext for option buttons

        Parameters
        ----------
        btntype: str
            The button type to set the help text for
        """
        logger.debug("Setting help")
        hlp = ""
        task = _("currently selected Task") if btntype[-1] == "2" else _("Project")
        if btntype.startswith("reload"):
            hlp = _("Reload {} from disk").format(task)
        if btntype == "new":
            hlp = _("Create a new {}...").format(task)
        if btntype.startswith("clear"):
            hlp = _("Reset {} to default").format(task)
        elif btntype.startswith("save") and "_" not in btntype:
            hlp = _("Save {}").format(task)
        elif btntype.startswith("save_as"):
            hlp = _("Save {} as...").format(task)
        elif btntype.startswith("load"):
            msg = task
            if msg.endswith("Task"):
                msg += _(" from a task or project file")
            hlp = _("Load {}...").format(msg)
        return hlp