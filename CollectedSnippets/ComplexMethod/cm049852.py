def _mail_track(self, tracked_fields, initial_values):
        """ For a given record, fields to check (tuple column name, column info)
        and initial values, return a valid command to create tracking values.

        :param dict tracked_fields: fields_get of updated fields on which
          tracking is checked and performed;
        :param dict initial_values: dict of initial values for each updated
          fields;

        :return: a tuple (changes, tracking_value_ids) where
          changes: set of updated column names; contains onchange tracked fields
          that changed;
          tracking_value_ids: a list of ORM (0, 0, values) commands to create
          ``mail.tracking.value`` records;

        Override this method on a specific model to implement model-specific
        behavior. Also consider inheriting from ``mail.thread``. """
        self.ensure_one()
        updated = set()
        tracking_value_ids = []

        fields_track_info = self._mail_track_order_fields(tracked_fields)
        for col_name, _sequence in fields_track_info:
            if col_name not in initial_values:
                continue
            initial_value = initial_values[col_name]
            new_value = (
                # get the properties definition with the value
                # (not just the dict with the value)
                field.convert_to_read(self[col_name], self)
                if (field := self._fields[col_name]).type == 'properties'
                else self[col_name]
            )
            if new_value == initial_value or (not new_value and not initial_value):  # because browse null != False
                continue

            if self._fields[col_name].type == "properties":
                definition_record_field = self._fields[col_name].definition_record
                if self[definition_record_field] == initial_values[definition_record_field]:
                    # track the change only if the parent changed
                    continue

                updated.add(col_name)
                tracking_value_ids.extend(
                    [0, 0, self.env['mail.tracking.value']._create_tracking_values_property(
                        property_, col_name, tracked_fields[col_name], self,
                    )]
                    # Show the properties in the same order as in the definition
                    for property_ in initial_value[::-1]
                    if property_['type'] not in ('separator', 'html') and property_.get('value')
                )
                continue

            updated.add(col_name)
            tracking_value_ids.append(
                [0, 0, self.env['mail.tracking.value']._create_tracking_values(
                    initial_value, new_value,
                    col_name, tracked_fields[col_name],
                    self
                )])

        return updated, tracking_value_ids