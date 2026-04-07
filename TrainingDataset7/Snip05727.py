def __str__(self):
        return "%s.%s" % (self.opts.app_label, self.__class__.__name__)