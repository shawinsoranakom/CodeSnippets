def tuple(self):
        "Get the tuple for each ring in this Polygon."
        return tuple(self[i].tuple for i in range(len(self)))