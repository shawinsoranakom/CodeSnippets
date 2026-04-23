def get_forward_related_filter(self, obj):
        """
        Return the keyword arguments that when supplied to
        self.model.object.filter(), would select all instances related through
        this field to the remote obj. This is used to build the querysets
        returned by related descriptors. obj is an instance of
        self.related_field.model.
        """
        return {
            "%s__%s" % (self.name, rh_field.name): getattr(obj, rh_field.attname)
            for _, rh_field in self.related_fields
        }