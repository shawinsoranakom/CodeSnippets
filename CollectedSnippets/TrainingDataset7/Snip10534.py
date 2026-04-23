def get_field(self, field_name):
        if (
            field_name == "_order"
            and self.options.get("order_with_respect_to") is not None
        ):
            field_name = self.options["order_with_respect_to"]
        return self.fields[field_name]