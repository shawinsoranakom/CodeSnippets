def delete(self, name):
        path, filename = os.path.split(name)
        dir_node = self._resolve(path, check_exists=False)
        if dir_node is None:
            return None
        dir_node.remove_child(filename)