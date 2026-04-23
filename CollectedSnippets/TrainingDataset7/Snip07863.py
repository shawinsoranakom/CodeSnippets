def __str__(self):
        result = super().__str__()
        return ("~%s" % result) if self.invert else result