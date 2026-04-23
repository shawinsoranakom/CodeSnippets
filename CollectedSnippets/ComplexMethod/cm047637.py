def _add_display_name(cls, values_list, env, value_keys=('value', 'default')):
        """Add the "display_name" for each many2one / many2many properties.

        Modify in place "values_list".

        :param values_list: List of properties definition and values
        :param env: environment
        """
        for property_definition in values_list:
            property_type = property_definition.get('type')
            property_model = property_definition.get('comodel')
            if not property_model:
                continue

            for value_key in value_keys:
                property_value = property_definition.get(value_key)

                if property_type == 'many2one' and property_value and isinstance(property_value, int):
                    try:
                        display_name = env[property_model].browse(property_value).display_name
                        property_definition[value_key] = (property_value, display_name)
                    except AccessError:
                        # protect from access error message, show an empty name
                        property_definition[value_key] = (property_value, None)
                    except MissingError:
                        property_definition[value_key] = False

                elif property_type == 'many2many' and property_value and is_list_of(property_value, int):
                    property_definition[value_key] = []
                    records = env[property_model].browse(property_value)
                    for record in records:
                        try:
                            property_definition[value_key].append((record.id, record.display_name))
                        except AccessError:
                            property_definition[value_key].append((record.id, None))
                        except MissingError:
                            continue