def remove_folder(self, folder):
        """Delete the named folder, which must be empty."""
        path = os.path.join(self._path, '.' + folder)
        for entry in os.listdir(os.path.join(path, 'new')) + \
                     os.listdir(os.path.join(path, 'cur')):
            if len(entry) < 1 or entry[0] != '.':
                raise NotEmptyError('Folder contains message(s): %s' % folder)
        for entry in os.listdir(path):
            if entry != 'new' and entry != 'cur' and entry != 'tmp' and \
               os.path.isdir(os.path.join(path, entry)):
                raise NotEmptyError("Folder contains subdirectory '%s': %s" %
                                    (folder, entry))
        for root, dirs, files in os.walk(path, topdown=False):
            for entry in files:
                os.remove(os.path.join(root, entry))
            for entry in dirs:
                os.rmdir(os.path.join(root, entry))
        os.rmdir(path)