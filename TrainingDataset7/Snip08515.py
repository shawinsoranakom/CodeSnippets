def listdir(self):
        directories, files = [], []
        for name, entry in self._children.items():
            if isinstance(entry, InMemoryDirNode):
                directories.append(name)
            else:
                files.append(name)
        return directories, files