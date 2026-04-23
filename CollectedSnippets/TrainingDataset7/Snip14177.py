def _subscribe_dir(self, directory, filenames):
        if not directory.exists():
            if not directory.parent.exists():
                logger.warning(
                    "Unable to watch directory %s as neither it or its parent exist.",
                    directory,
                )
                return
            prefix = "files-parent-%s" % directory.name
            filenames = ["%s/%s" % (directory.name, filename) for filename in filenames]
            directory = directory.parent
            expression = ["name", filenames, "wholename"]
        else:
            prefix = "files"
            expression = ["name", filenames]
        self._subscribe(directory, "%s:%s" % (prefix, directory), expression)