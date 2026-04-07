def cleanup(self):
        """
        Remove a preprocessed copy of a translatable file (if any).
        """
        if self.is_templatized:
            # This check is needed for the case of a symlinked file and its
            # source being processed inside a single group (locale dir);
            # removing either of those two removes both.
            if os.path.exists(self.work_path):
                os.unlink(self.work_path)