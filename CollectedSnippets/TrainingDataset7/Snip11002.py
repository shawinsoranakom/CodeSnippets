def _description(self):
        return _("Field of type: %(field_type)s") % {
            "field_type": self.__class__.__name__
        }