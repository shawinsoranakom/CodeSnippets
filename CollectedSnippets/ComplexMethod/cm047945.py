def _handle_fallback_values(self, import_field, input_file_data, fallback_values):
        """
        If there are fallback values, this method will replace the input file
        data value if it does not match the possible values for the given field.
        This is only valid for boolean and selection fields.

        .. note::

            We can consider that we need to retrieve the selection values for
            all the fields in fallback_values, as if they are present, it's because
            there was already a conflict during first import run and user had to
            select a fallback value for the field.

        :param list import_field: ordered list of field that have been matched to import data
        :param list input_file_data: ordered list of values (list) that need to be imported in
            the given import_fields
        :param dict fallback_values:

            contains all the fields that have been tagged by the user to use a
            specific fallback value in case the value to import does not match
            values accepted by the field (selection or boolean) e.g.::

                {
                    'fieldName': {
                        'fallback_value': fallback_value,
                        'field_model': field_model,
                        'field_type': field_type
                    },
                    'state': {
                        'fallback_value': 'draft',
                        'field_model': field_model,
                        'field_type': 'selection'
                    },
                    'active': {
                        'fallback_value': 'true',
                        'field_model': field_model,
                        'field_type': 'boolean'
                    }
                }
        """
        # add possible selection values into our fallback dictionary for fields of type "selection"
        for field_string in fallback_values:
            if fallback_values[field_string]['field_type'] != "selection":
                continue
            field_path = field_string.split('/')
            target_field = field_path[-1]
            target_model = self.env[fallback_values[field_string]['field_model']]

            selection_values = [value.lower() for (key, value) in target_model.fields_get([target_field])[target_field]['selection']]
            fallback_values[field_string]['selection_values'] = selection_values

        # check fallback values
        for record_index, records in enumerate(input_file_data):
            for column_index, value in enumerate(records):
                field = import_field[column_index]

                if field in fallback_values:
                    fallback_value = fallback_values[field]['fallback_value']
                    # Boolean
                    if fallback_values[field]['field_type'] == "boolean":
                        value = value if value.lower() in ('0', '1', 'true', 'false') else fallback_value
                    # Selection
                    elif fallback_values[field]['field_type'] == "selection" and value.lower() not in fallback_values[field]["selection_values"]:
                        value = fallback_value if fallback_value != 'skip' else None  # don't set any value if we skip

                    input_file_data[record_index][column_index] = value

        return input_file_data