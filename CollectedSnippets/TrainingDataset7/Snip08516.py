def remove_child(self, name):
        if name in self._children:
            self._update_accessed_time()
            self._update_modified_time()
            del self._children[name]