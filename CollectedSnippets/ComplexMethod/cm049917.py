def _tracking_value_format_model(self, model):
        """ Return structure and formatted data structure to be used by chatter
        to display tracking values. Order it according to asked display, aka
        ascending sequence (and field name).

        :returns: for each tracking value in self, their formatted display
          values given as a dict;
        :rtype: list[dict]
        """
        if not self:
            return []

        # fetch model-based information
        if model:
            TrackedModel = self.env[model]
            tracked_fields = TrackedModel.fields_get(self.field_id.mapped('name'), attributes={'digits', 'string', 'type'})
            model_sequence_info = dict(TrackedModel._mail_track_order_fields(tracked_fields)) if model else {}
        else:
            tracked_fields, model_sequence_info = {}, {}

        # generate sequence of trackings
        fields_sequence_map = dict(
            {
                tracking.field_info['name']: tracking.field_info.get('sequence', 100)
                for tracking in self.filtered('field_info')
            },
            **model_sequence_info,
        )
        # generate dict of field information, if available
        fields_col_info = (
            tracking.field_id.ttype != 'properties'
            and tracked_fields.get(tracking.field_id.name)
            or {
                'string': tracking.field_info['desc'] if tracking.field_info else self.env._('Unknown'),
                'type': tracking.field_info['type'] if tracking.field_info else 'char',
            } for tracking in self
        )

        def sort_tracking_info(tracking_info_tuple):
            tracking = tracking_info_tuple[0]
            field_name = tracking.field_id.name or (tracking.field_info['name'] if tracking.field_info else 'unknown')
            return (
                fields_sequence_map.get(field_name, 100),
                tracking.field_id.ttype == 'properties',
                field_name,
            )

        formatted = [
            {
                'id': tracking.id,
                'fieldInfo': {
                    'changedField': col_info['string'],
                    'currencyId': tracking.currency_id.id,
                    'floatPrecision': col_info.get('digits'),
                    'fieldType': col_info['type'],
                    'isPropertyField': tracking.field_id.ttype == 'properties',
                },
                'newValue': tracking._format_display_value(col_info['type'], new=True)[0],
                'oldValue': tracking._format_display_value(col_info['type'], new=False)[0],
            }
            for tracking, col_info in sorted(zip(self, fields_col_info), key=sort_tracking_info)
        ]
        return formatted