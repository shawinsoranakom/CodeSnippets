def write(self, content):
        raise OSError("This %s instance is not writable" % self.__class__.__name__)