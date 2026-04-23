def _check_valid(self, filename: str, for_restore: bool = False) -> bool:
        """ Check if the passed in filename is valid for a backup or restore operation.

        Parameters
        ----------
        filename: str
            The filename that is to be checked for backup or restore
        for_restore: bool, optional
            ``True`` if the checks are to be performed for restoring a model, ``False`` if the
            checks are to be performed for backing up a model. Default: ``False``

        Returns
        -------
        bool
            ``True`` if the given file is valid for a backup/restore operation otherwise ``False``
        """
        fullpath = os.path.join(self.model_dir, filename)
        if not filename.startswith(self.model_name):
            # Any filename that does not start with the model name are invalid
            # for all operations
            retval = False
        elif for_restore and filename.endswith(".bk"):
            # Only filenames ending in .bk are valid for restoring
            retval = True
        elif not for_restore and ((os.path.isfile(fullpath) and not filename.endswith(".bk")) or
                                  (os.path.isdir(fullpath) and
                                   filename == f"{self.model_name}_logs")):
            # Only filenames that do not end with .bk or folders that are the logs folder
            # are valid for backup
            retval = True
        else:
            retval = False
        logger.debug("'%s' valid for backup operation: %s", filename, retval)
        return retval