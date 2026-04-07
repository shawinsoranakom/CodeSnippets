def description(self):
        if self.max_length is not None:
            return _("String (up to %(max_length)s)")
        else:
            return _("String (unlimited)")