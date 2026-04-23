def _set(self, key, value):
        """
        Sets a value and saves the old value so it can be restored when
        we pop the frame. A sentinel object, _cell_delete_obj, indicates that
        the key was previously empty and should just be deleted.
        """

        # save the old value (or mark that it didn't exist)
        self.stack.append((key, self.values.get(key, self._cell_delete_obj)))

        # write the new value
        self.values[key] = value