def _validate_properties_definition(self, properties_definition, env):
        """Raise an error if the property definition is not valid."""
        allowed_keys = self.ALLOWED_KEYS + env["base"]._additional_allowed_keys_properties_definition()

        env["base"]._validate_properties_definition(properties_definition, self)

        properties_names = set()

        for property_definition in properties_definition:
            for property_parameter, allowed_types in self.PROPERTY_PARAMETERS_MAP.items():
                if property_definition.get('type') not in allowed_types and property_parameter in property_definition:
                    raise ValueError(f'Invalid property parameter {property_parameter!r}')

            property_definition_keys = set(property_definition.keys())

            invalid_keys = property_definition_keys - set(allowed_keys)
            if invalid_keys:
                raise ValueError(
                    'Some key are not allowed for a properties definition [%s].' %
                    ', '.join(invalid_keys),
                )

            check_property_field_value_name(property_definition['name'])

            required_keys = set(self.REQUIRED_KEYS) - property_definition_keys
            if required_keys:
                raise ValueError(
                    'Some key are missing for a properties definition [%s].' %
                    ', '.join(required_keys),
                )

            property_type = property_definition.get('type')
            property_name = property_definition.get('name')
            if not property_name or property_name in properties_names:
                raise ValueError(f'The property name {property_name!r} is not set or duplicated.')
            properties_names.add(property_name)

            if property_type == 'html' and not property_name.endswith('_html'):
                raise ValueError("HTML property name should end with `_html`.")

            if property_type != 'html' and property_name.endswith('_html'):
                raise ValueError("Only HTML properties can have the `_html` suffix.")

            if property_type and property_type not in Properties.ALLOWED_TYPES:
                raise ValueError(f'Wrong property type {property_type!r}.')

            if property_type == 'html' and (default := property_definition.get('default')):
                property_definition['default'] = html_sanitize(default, **Properties.HTML_SANITIZE_OPTIONS)

            model = property_definition.get('comodel')
            if model and (model not in env or env[model].is_transient() or env[model]._abstract):
                raise ValueError(f'Invalid model name {model!r}')

            property_selection = property_definition.get('selection')
            if property_selection:
                if (not is_list_of(property_selection, (list, tuple))
                   or not all(len(selection) == 2 for selection in property_selection)):
                    raise ValueError(f'Wrong options {property_selection!r}.')

                all_options = [option[0] for option in property_selection]
                if len(all_options) != len(set(all_options)):
                    duplicated = set(filter(lambda x: all_options.count(x) > 1, all_options))
                    raise ValueError(f'Some options are duplicated: {", ".join(duplicated)}.')

            property_tags = property_definition.get('tags')
            if property_tags:
                if (not is_list_of(property_tags, (list, tuple))
                   or not all(len(tag) == 3 and isinstance(tag[2], int) for tag in property_tags)):
                    raise ValueError(f'Wrong tags definition {property_tags!r}.')

                all_tags = [tag[0] for tag in property_tags]
                if len(all_tags) != len(set(all_tags)):
                    duplicated = set(filter(lambda x: all_tags.count(x) > 1, all_tags))
                    raise ValueError(f'Some tags are duplicated: {", ".join(duplicated)}.')