def _hash_text(cls, text):
        h = hashlib.new(cls.hash_algorithm, usedforsecurity=False)
        h.update(text.encode("utf-8"))
        return h.hexdigest()