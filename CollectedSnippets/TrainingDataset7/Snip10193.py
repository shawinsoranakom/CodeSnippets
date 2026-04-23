def __hash__(self):
        return hash("%s.%s" % (self.app_label, self.name))