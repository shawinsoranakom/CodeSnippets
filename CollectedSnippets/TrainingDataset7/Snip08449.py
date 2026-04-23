def write(self, data):
        self.__dict__.pop("size", None)  # Clear the computed size.
        return self.file.write(data)