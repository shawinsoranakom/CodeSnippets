def save(self):
        for name, data in self._data.items():
            Image.open(io.BytesIO(data)).save("/tmp/%s" % name)