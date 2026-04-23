def file_hash(self, name, content=None):
        """
        Return a hash of the file with the given name and optional content.
        """
        if content is None:
            return None
        hasher = md5(usedforsecurity=False)
        for chunk in content.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()[:12]