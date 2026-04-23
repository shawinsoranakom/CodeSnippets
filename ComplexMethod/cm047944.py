def _handle_multi_mapping(self, import_fields, input_file_data):
        """ This method handles multiple mapping on the same field.

        It will return the list of the mapped fields and the concatenated data for each field:

        - If two column are mapped on the same text or char field, they will end up
          in only one column, concatenated via space (char) or new line (text).
        - The same logic is used for many2many fields. Multiple values can be
          imported if they are separated by ``,``.

        Input/output Example:

        input data
            .. code-block:: python

                [
                    ["Value part 1", "1", "res.partner_id1", "Value part 2"],
                    ["I am", "1", "res.partner_id1", "Batman"],
                ]

        import_fields
            ``[desc, some_number, partner, desc]``

        output merged_data
            .. code-block:: python

                [
                    ["Value part 1 Value part 2", "1", "res.partner_id1"],
                    ["I am Batman", "1", "res.partner_id1"],
                ]
        fields
            ``[desc, some_number, partner]``
        """
        # Get fields and their occurrences indexes
        # Among the fields that have been mapped, we get their corresponding mapped column indexes
        # as multiple fields could have been mapped to multiple columns.
        mapped_field_indexes = {}
        for idx, field in enumerate(field for field in import_fields if field):
            mapped_field_indexes.setdefault(field, list()).append(idx)
        import_fields = list(mapped_field_indexes.keys())
        import_options = self.env.context.get('import_options', {})

        # recreate data and merge duplicates (applies only on text or char fields)
        # Also handles multi-mapping on "field of relation fields".
        merged_data = []
        for record in input_file_data:
            new_record = []
            for fields, indexes in mapped_field_indexes.items():
                split_fields = fields.split('/')
                target_field = split_fields[-1]

                # get target_field type (on target model)
                target_model = self.res_model
                for field in split_fields:
                    # if not on the last hierarchy level, retarget the model.
                    # Also check if the field exists to silently ignore properties field and
                    # since we don't have the definition here anyway.
                    if field != target_field and field in self.env[target_model]:
                        target_model = self.env[target_model][field]._name

                field = self.env[target_model]._fields.get(target_field.split('.')[0])
                field_type = field.type if field else ''

                # merge data if necessary
                if field_type in CONCAT_SEPARATOR_IMPORT:
                    separator = CONCAT_SEPARATOR_IMPORT[field_type]
                    if field_type != 'many2many':
                        # Trim trailing whitespaces before joining
                        trim = field_type == 'char' and field.trim
                        new_record.append(
                            separator.join(
                                self._stringify_date_like_objects(record[idx], import_options, trim)
                                for idx in indexes if record[idx]
                            )
                        )
                    else:
                        new_record.append(separator.join(record[idx] for idx in indexes if record[idx]))
                elif field_type == 'properties':
                    # for property fields date and datetime objects are not suitable for JSON values
                    new_record.append(self._stringify_date_like_objects(record[indexes[0]], import_options))
                else:
                    new_record.append(record[indexes[0]])

            merged_data.append(new_record)

        return import_fields, merged_data