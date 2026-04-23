def _add_default_values(self, env, values):
        """Read the properties definition to add default values.

        Default values are defined on the container in the 'default' key of
        the definition.

        :param env: environment
        :param values: All values that will be written on the record
        :return: Return the default values in the "dict" format
        """
        properties_values = values.get(self.name) or {}

        if isinstance(properties_values, Property):
            properties_values = properties_values._values

        if not values.get(self.definition_record):
            # container is not given in the value, can not find properties definition
            return {}

        container_id = values[self.definition_record]
        if not isinstance(container_id, (int, BaseModel)):
            raise ValueError(f"Wrong container value {container_id!r}")

        if isinstance(container_id, int):
            # retrieve the container record
            current_model = env[self.model_name]
            definition_record_field = current_model._fields[self.definition_record]
            container_model_name = definition_record_field.comodel_name
            container_id = env[container_model_name].sudo().browse(container_id)

        properties_definition = container_id[self.definition_record_field]
        if not (properties_definition or (
            isinstance(properties_values, list)
            and any(d.get('definition_changed') for d in properties_values)
        )):
            # If a parent is set without properties, we might want to change its definition
            # when we create the new record. But if we just set the value without changing
            # the definition, in that case we can just ignored the passed values
            return {}

        assert isinstance(properties_values, (list, dict))
        if isinstance(properties_values, list):
            self._remove_display_name(properties_values)
            properties_list_values = properties_values
        else:
            properties_list_values = self._dict_to_list(properties_values, properties_definition)

        for properties_value in properties_list_values:
            if properties_value.get('value') is None:
                property_name = properties_value.get('name')
                context_key = f"default_{self.name}.{property_name}"
                if property_name and context_key in env.context:
                    default = env.context[context_key]
                else:
                    default = properties_value.get('default')
                if default:
                    properties_value['value'] = default

        return properties_list_values