def order_fields(self, field_order):
        """
        Rearrange the fields according to field_order.

        field_order is a list of field names specifying the order. Append
        fields not included in the list in the default order for backward
        compatibility with subclasses not overriding field_order. If
        field_order is None, keep all fields in the order defined in the class.
        Ignore unknown fields in field_order to allow disabling fields in form
        subclasses without redefining ordering.
        """
        if field_order is None:
            return
        fields = {}
        for key in field_order:
            try:
                fields[key] = self.fields.pop(key)
            except KeyError:  # ignore unknown fields
                pass
        fields.update(self.fields)  # add remaining fields in original order
        self.fields = fields