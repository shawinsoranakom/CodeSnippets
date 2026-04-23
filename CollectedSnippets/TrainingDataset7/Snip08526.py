def _save(self, name, content):
        file_node = self._resolve(
            name, create_if_missing=True, leaf_cls=InMemoryFileNode
        )
        fd = None
        for chunk in content.chunks():
            if fd is None:
                mode = "wb" if isinstance(chunk, bytes) else "wt"
                fd = file_node.open(mode)
            fd.write(chunk)

        if hasattr(content, "temporary_file_path"):
            os.remove(content.temporary_file_path())

        file_node.modified_time = now()
        return self._relative_path(name).replace("\\", "/")