def get_modified_time(self, name):
        file_node = self._resolve(name)
        return file_node.modified_time