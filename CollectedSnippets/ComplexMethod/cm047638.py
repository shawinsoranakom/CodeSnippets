def _remove_display_name(cls, values_list, value_key='value'):
        """Remove the display name received by the web client for the relational properties.

        Modify in place "values_list".

        - many2one: (35, 'Bob') -> 35
        - many2many: [(35, 'Bob'), (36, 'Alice')] -> [35, 36]

        :param values_list: List of properties definition with properties value
        :param value_key: In which dict key we need to remove the display name
        """
        for property_definition in values_list:
            if not isinstance(property_definition, dict) or not property_definition.get('name'):
                continue

            property_value = property_definition.get(value_key)
            if not property_value:
                continue

            property_type = property_definition.get('type')

            if property_type == 'many2one' and has_list_types(property_value, [int, (str, NoneType)]):
                property_definition[value_key] = property_value[0]

            elif property_type == 'many2many':
                if is_list_of(property_value, (list, tuple)):
                    # [(35, 'Admin'), (36, 'Demo')] -> [35, 36]
                    property_definition[value_key] = [
                        many2many_value[0]
                        for many2many_value in property_value
                    ]