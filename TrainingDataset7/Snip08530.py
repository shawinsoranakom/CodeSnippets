def listdir(self, path):
        node = self._resolve(path, leaf_cls=InMemoryDirNode)
        return node.listdir()