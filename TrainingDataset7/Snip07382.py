def insert(self, index, val):
        "Standard list insert method"
        if not isinstance(index, int):
            raise TypeError("%s is not a legal index" % index)
        self[index:index] = [val]