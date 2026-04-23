def write(self, records, value):
        """Check if the properties definition has been changed.

        To avoid extra SQL queries used to detect definition change, we add a
        flag in the properties list. Parent update is done only when this flag
        is present, delegating the check to the caller (generally web client).

        For deletion, we need to keep the removed property definition in the
        list to be able to put the delete flag in it. Otherwise we have no way
        to know that a property has been removed.
        """
        if isinstance(value, str):
            value = json.loads(value)

        if isinstance(value, Property):
            value = value._values

        if len(records[self.definition_record]) > 1 and value:
            raise UserError(records.env._("Updating records with different property fields definitions is not supported. Update by separate definition instead."))

        if isinstance(value, dict):
            # don't need to write on the container definition
            return super().write(records, value)

        definition_changed = any(
            definition.get('definition_changed')
            or definition.get('definition_deleted')
            for definition in (value or [])
        )
        if definition_changed:
            value = [
                definition for definition in value
                if not definition.get('definition_deleted')
            ]
            for definition in value:
                definition.pop('definition_changed', None)

            # update the properties definition on the container
            container = records[self.definition_record]
            if container:
                properties_definition = copy.deepcopy(value)
                for property_definition in properties_definition:
                    property_definition.pop('value', None)
                container[self.definition_record_field] = properties_definition

                _logger.info('Properties field: User #%i changed definition of %r', records.env.user.id, container)

        return super().write(records, value)