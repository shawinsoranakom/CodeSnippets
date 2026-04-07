def a(self):
        "'a.m.' or 'p.m.'"
        if self.data.hour > 11:
            return _("p.m.")
        return _("a.m.")