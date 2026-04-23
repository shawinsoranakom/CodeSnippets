def get_accessed_time(self, name):
        file_node = self._resolve(name)
        return file_node.accessed_time