def get_related_field(self):
        """
        Return the field in the 'to' object to which this relationship is tied.
        Provided for symmetry with ManyToOneRel.
        """
        opts = self.through._meta
        if self.through_fields:
            field = opts.get_field(self.through_fields[0])
        else:
            for field in opts.fields:
                rel = getattr(field, "remote_field", None)
                if rel and rel.model == self.model:
                    break
        return field.foreign_related_fields[0]