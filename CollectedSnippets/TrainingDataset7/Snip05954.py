def has_related_field_in_list_display(self):
        for field_name in self.list_display:
            try:
                field = self.lookup_opts.get_field(field_name)
            except FieldDoesNotExist:
                pass
            else:
                if isinstance(field.remote_field, ManyToOneRel):
                    # <FK>_id field names don't require a join.
                    if field_name != field.attname:
                        return True
        return False