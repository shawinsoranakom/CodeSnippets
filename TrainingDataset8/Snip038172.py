def __contains__(self, key: str) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True