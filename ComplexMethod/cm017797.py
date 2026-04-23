def get_field_type(self, connection, table_name, row):
        """
        Given the database connection, the table name, and the cursor row
        description, this routine will return the given field type name, as
        well as any additional keyword parameters and notes for the field.
        """
        field_params = {}
        field_notes = []

        try:
            field_type = connection.introspection.get_field_type(row.type_code, row)
        except KeyError:
            field_type = "TextField"
            field_notes.append("This field type is a guess.")

        # Add max_length for all CharFields.
        if field_type == "CharField" and row.display_size:
            if (size := int(row.display_size)) and size > 0:
                field_params["max_length"] = size

        if field_type in {"CharField", "TextField"} and row.collation:
            field_params["db_collation"] = row.collation

        if field_type == "DecimalField" and (
            # This can generate DecimalFields with only one of max_digits and
            # decimal_fields specified. This configuration would be incorrect,
            # but nothing more correct could be generated.
            row.precision is not None
            or row.scale is not None
        ):
            field_params["max_digits"] = row.precision
            field_params["decimal_places"] = row.scale

        return field_type, field_params, field_notes