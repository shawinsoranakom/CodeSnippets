def append(self, val):
        "Standard list append method"
        self[len(self) :] = [val]