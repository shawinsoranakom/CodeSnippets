def get_created_time(self, name):
        file_node = self._resolve(name)
        return file_node.created_time