def _open(self, name, mode="rb"):
        create_if_missing = "w" in mode
        file_node = self._resolve(
            name, create_if_missing=create_if_missing, leaf_cls=InMemoryFileNode
        )
        return file_node.open(mode)