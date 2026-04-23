def clear_dir(self, path):
        """
        Delete the given relative path using the destination storage backend.
        """
        if not self.storage.exists(path):
            return

        dirs, files = self.storage.listdir(path)
        for f in files:
            fpath = os.path.join(path, f)
            if self.dry_run:
                self.log("Pretending to delete '%s'" % fpath, level=2)
                self.deleted_files.append(fpath)
            else:
                self.log("Deleting '%s'" % fpath, level=2)
                self.deleted_files.append(fpath)
                try:
                    full_path = self.storage.path(fpath)
                except NotImplementedError:
                    self.storage.delete(fpath)
                else:
                    if not os.path.exists(full_path) and os.path.lexists(full_path):
                        # Delete broken symlinks
                        os.unlink(full_path)
                    else:
                        self.storage.delete(fpath)
        for d in dirs:
            self.clear_dir(os.path.join(path, d))