def A(self):
        "'AM' or 'PM'"
        if self.data.hour > 11:
            return _("PM")
        return _("AM")