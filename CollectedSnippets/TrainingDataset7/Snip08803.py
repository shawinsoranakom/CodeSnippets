def work_path(self):
        """
        Path to a file which is being fed into GNU gettext pipeline. This may
        be either a translatable or its preprocessed version.
        """
        if not self.is_templatized:
            return self.path
        filename = f"{self.translatable.file}.py"
        return os.path.join(self.translatable.dirpath, filename)