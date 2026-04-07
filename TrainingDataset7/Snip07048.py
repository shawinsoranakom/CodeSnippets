def field_types(self):
        """
        Return a list of the types of fields in this Layer. For example,
        return the list [OFTInteger, OFTReal, OFTString] for an OGR layer that
        has an integer, a floating-point, and string fields.
        """
        return [
            OGRFieldTypes[capi.get_field_type(capi.get_field_defn(self._ldefn, i))]
            for i in range(self.num_fields)
        ]