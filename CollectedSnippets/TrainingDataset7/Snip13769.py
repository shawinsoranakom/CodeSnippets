def _hash_item(self, item, key):
        text = "{}{}".format(self.seed, key(item))
        return self._hash_text(text)