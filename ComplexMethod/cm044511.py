def _set_filename(self, filename=None, sess_type="project"):
        """ Set the :attr:`_filename` attribute.

        :attr:`_filename` is set either from a given filename or the result from
        a :attr:`_file_handler`.

        Parameters
        ----------
        filename: str, optional
            An optional filename. If given then this filename will be used otherwise it will be
            collected by a :attr:`_file_handler`

        sess_type: {all, project, task}, optional
            The session type that the filename is being set for. Dictates the type of file handler
            that is opened.

        Returns
        -------
        bool: `True` if filename has been successfully set otherwise ``False``
        """
        logger.debug("filename: '%s', sess_type: '%s'", filename, sess_type)
        handler = f"config_{sess_type}"

        if filename is None:
            logger.debug("Popping file handler")
            cfgfile = self._file_handler("open", handler).return_file
            if not cfgfile:
                logger.debug("No filename given")
                return False
            filename = cfgfile.name
            cfgfile.close()

        if not os.path.isfile(filename):
            msg = f"File does not exist: '{filename}'"
            logger.error(msg)
            return False
        ext = os.path.splitext(filename)[1]
        if (sess_type == "project" and ext != ".fsw") or (sess_type == "task" and ext != ".fst"):
            logger.debug("Invalid file extension for session type: (sess_type: '%s', "
                         "extension: '%s')", sess_type, ext)
            return False
        logger.debug("Setting filename: '%s'", filename)
        self._filename = filename
        return True