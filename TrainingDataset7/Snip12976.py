def writelines(self, lines):
        raise OSError("This %s instance is not writable" % self.__class__.__name__)