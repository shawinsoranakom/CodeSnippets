def get_ordering_field(self, field_name):
        """
        Return the proper model field name corresponding to the given
        field_name to use for ordering. field_name may either be the name of a
        proper model field, possibly across relations, or the name of a method
        (on the admin or model) or a callable with the 'admin_order_field'
        attribute. Return None if no proper model field name can be matched.
        """
        try:
            field = self.lookup_opts.get_field(field_name)
            return field.name
        except FieldDoesNotExist:
            # See whether field_name is a name of a non-field
            # that allows sorting.
            if callable(field_name):
                attr = field_name
            elif hasattr(self.model_admin, field_name):
                attr = getattr(self.model_admin, field_name)
            else:
                try:
                    attr = getattr(self.model, field_name)
                except AttributeError:
                    if LOOKUP_SEP in field_name:
                        return field_name
                    raise
            if isinstance(attr, property) and hasattr(attr, "fget"):
                attr = attr.fget
            return getattr(attr, "admin_order_field", None)