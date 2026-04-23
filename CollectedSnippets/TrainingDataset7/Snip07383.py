def pop(self, index=-1):
        "Standard list pop method"
        result = self[index]
        del self[index]
        return result