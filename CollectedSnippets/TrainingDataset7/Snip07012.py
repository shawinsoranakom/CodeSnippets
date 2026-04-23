def tuple(self):
        "Return the tuple representation of this LineString."
        return tuple(self[i] for i in range(len(self)))