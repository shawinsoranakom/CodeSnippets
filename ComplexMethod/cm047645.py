def get_property(record):
            property_value = self.__get__(record.with_context(property_selection_get_key=True))
            value = property_value.get(property_name)
            if value:
                return value
            # find definition to check the type
            for definition in self._get_properties_definition(record) or ():
                if definition.get('name') == property_name:
                    break
            else:
                # definition not found
                return value or False

            if not value and definition['type'] in ('many2one', 'many2many'):
                return record.env.get(definition.get('comodel'))
            return value