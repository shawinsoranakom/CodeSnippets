def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        return True