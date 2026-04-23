def assertTracking(self, message, data, strict=False):
        tracking_values = message.sudo().tracking_value_ids
        if strict:
            self.assertEqual(len(tracking_values), len(data),
                             'Tracking: tracking does not match')

        suffix_mapping = {
            'boolean': 'integer',
            'char': 'char',
            'date': 'datetime',
            'datetime': 'datetime',
            'integer': 'integer',
            'float': 'float',
            'many2many': 'char',
            'one2many': 'char',
            'selection': 'char',
            'text': 'text',
        }
        for field_name, value_type, old_value, new_value in data:
            tracking = tracking_values.filtered(lambda track: track.field_id.name == field_name)
            self.assertEqual(len(tracking), 1, f'Tracking: not found for {field_name}')
            msg_base = f'Tracking: {field_name} ({value_type}: '
            if value_type in suffix_mapping:
                old_value_fname = f'old_value_{suffix_mapping[value_type]}'
                new_value_fname = f'new_value_{suffix_mapping[value_type]}'
                self.assertEqual(tracking[old_value_fname], old_value,
                                 msg_base + f'expected {old_value}, received {tracking[old_value_fname]})')
                self.assertEqual(tracking[new_value_fname], new_value,
                                 msg_base + f'expected {new_value}, received {tracking[new_value_fname]})')
            if value_type == 'many2one':
                self.assertEqual(tracking.old_value_integer, old_value and old_value.id or False)
                self.assertEqual(tracking.new_value_integer, new_value and new_value.id or False)
                self.assertEqual(tracking.old_value_char, old_value and old_value.display_name or '')
                self.assertEqual(tracking.new_value_char, new_value and new_value.display_name or '')
            elif value_type == 'monetary':
                new_value, currency = new_value
                self.assertEqual(tracking.currency_id, currency)
                self.assertEqual(tracking.old_value_float, old_value)
                self.assertEqual(tracking.new_value_float, new_value)
            if value_type not in suffix_mapping and value_type not in {'many2one', 'monetary'}:
                self.assertEqual(1, 0, f'Tracking: unsupported tracking test on {value_type}')