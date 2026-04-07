def type_name(self):
        "Return the OGR field type name for this Field."
        return capi.get_field_type_name(self.type)