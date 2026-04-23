def index(self, val):
        "Standard list index method"
        for i in range(0, len(self)):
            if self[i] == val:
                return i
        raise ValueError("%s not found in object" % val)