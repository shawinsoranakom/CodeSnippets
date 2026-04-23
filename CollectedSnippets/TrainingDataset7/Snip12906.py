def close(self):
        if hasattr(self, "_files"):
            for f in chain.from_iterable(list_[1] for list_ in self._files.lists()):
                f.close()