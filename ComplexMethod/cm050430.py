def _format_properties(self):
        """Format the properties to build the merge message.

        Return a list of dict containing the label, and a value key if there's only
        one value, or a "values" key if we have multiple values (e.g. many2many, tags).

        E.G.
            [{
                'label': 'My Partner',
                'value': 'Alice',
            }, {
                'label': 'My Partners',
                'values': [
                    {'name': 'Alice'},
                    {'name': 'Bob'},
                ],
            }, {
                'label': 'My Tags',
                'values': [
                    {'name': 'A', 'color': 1},
                    {'name': 'C', 'color': 3},
                ],
            }]
        """
        self.ensure_one()
        # read to have the display names already in the value
        properties = self.read(['lead_properties'])[0]['lead_properties']

        formatted = []
        for definition in properties:
            label = definition.get('string')
            value = definition.get('value')
            property_type = definition['type']
            if not value and property_type != 'boolean':
                continue

            property_dict = {'label': label}
            if property_type == 'boolean':
                property_dict['value'] = _('Yes') if value else _('No')
            elif value and property_type == 'many2one':
                property_dict['value'] = value[1]
            elif value and property_type == 'many2many':
                # show many2many in badge
                property_dict['values'] = [{'name': rec[1]} for rec in value]
            elif value and property_type in ['selection', 'tags']:
                # retrieve the option label from the value
                options = {
                    option[0]: option[1:]
                    for option in (definition.get(property_type) or [])
                }
                if property_type == 'selection':
                    value = options.get(value)
                    property_dict['value'] = value[0] if value else None
                else:
                    property_dict['values'] = [{
                        'name': options[tag][0],
                        'color': options[tag][1],
                        } for tag in value if tag in options
                    ]
            else:
                property_dict['value'] = value

            formatted.append(property_dict)

        return formatted