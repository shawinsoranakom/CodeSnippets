def _parse_json_types(cls, values_list, env, res_ids_per_model):
        """Parse the value stored in the JSON.

        Check for records existence, if we removed a selection option, ...
        Modify in place "values_list".

        :param values_list: List of properties definition and values
        :param env: environment
        """
        for property_definition in values_list:
            property_value = property_definition.get('value')
            property_type = property_definition.get('type')
            res_model = property_definition.get('comodel')

            if property_type not in cls.ALLOWED_TYPES:
                raise ValueError(f'Wrong property type {property_type!r}')

            if property_value is None:
                continue

            if property_type == 'boolean':
                # E.G. convert zero to False
                property_value = bool(property_value)

            elif property_type in ('char', 'text') and not isinstance(property_value, str):
                property_value = False

            elif property_value and property_type == 'selection':
                # check if the selection option still exists
                options = property_definition.get('selection') or []
                options = {option[0] for option in options if option or ()}  # always length 2
                if property_value not in options:
                    # maybe the option has been removed on the container
                    property_value = False

            elif property_value and property_type == 'tags':
                # remove all tags that are not defined on the container
                all_tags = {tag[0] for tag in property_definition.get('tags') or ()}
                property_value = [tag for tag in property_value if tag in all_tags]

            elif property_type == 'many2one':
                if not isinstance(property_value, int) \
                        or res_model not in env \
                        or property_value not in res_ids_per_model[res_model]:
                    property_value = False

            elif property_type == 'many2many':
                if not is_list_of(property_value, int):
                    property_value = []

                elif len(property_value) != len(set(property_value)):
                    # remove duplicated value and preserve order
                    property_value = list(dict.fromkeys(property_value))

                property_value = [
                    id_ for id_ in property_value
                    if id_ in res_ids_per_model[res_model]
                ] if res_model in env else []

            elif property_type == 'html':
                # field name should end with `_html` to be legit and sanitized,
                # otherwise do not trust the value and force False
                property_value = property_definition['name'].endswith('_html') and property_value

            property_definition['value'] = property_value