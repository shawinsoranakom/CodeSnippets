def _list_to_dict(cls, values_list):
        """Convert a list of properties with definition into a dict {name: value}.

        To not repeat data in database, we only store the value of each property on
        the child. The properties definition is stored on the container.

        E.G.
            Input list:
            [{
                'name': '3adf37f3258cfe40',
                'string': 'Color Code',
                'type': 'char',
                'default': 'blue',
                'value': 'red',
            }, {
                'name': 'aa34746a6851ee4e',
                'string': 'Partner',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'value': [1337, 'Bob'],
            }]

            Output dict:
            {
                '3adf37f3258cfe40': 'red',
                'aa34746a6851ee4e': 1337,
            }

        :param values_list: List of properties definition and value
        :return: Generate a dict {name: value} from this definitions / values list
        """
        if not is_list_of(values_list, dict):
            raise ValueError(f'Wrong properties value {values_list!r}')

        cls._add_missing_names(values_list)

        dict_value = {}
        for property_definition in values_list:
            property_value = property_definition.get('value')
            property_type = property_definition.get('type')
            property_model = property_definition.get('comodel')
            if property_value is None:
                # Do not store None key
                continue

            if property_type not in ('integer', 'float') or property_value != 0:
                property_value = property_value or False
            if property_type in ('many2one', 'many2many') and property_model and property_value:
                # check that value are correct before storing them in database
                if property_type == 'many2many' and property_value and not is_list_of(property_value, int):
                    raise ValueError(f"Wrong many2many value {property_value!r}")

                if property_type == 'many2one' and not isinstance(property_value, int):
                    raise ValueError(f"Wrong many2one value {property_value!r}")

            dict_value[property_definition['name']] = property_value

        return dict_value