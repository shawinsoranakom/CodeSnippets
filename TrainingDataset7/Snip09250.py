def get_field_type(self, data_type, description):
        """
        Hook for a database backend to use the cursor description to
        match a Django field type to a database column.

        For Oracle, the column data_type on its own is insufficient to
        distinguish between a FloatField and IntegerField, for example.
        """
        return self.data_types_reverse[data_type]