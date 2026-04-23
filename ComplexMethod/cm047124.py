def __setitem__(self, field_name, value):
        """ Set the given field to the given value, and proceed with the expected onchanges. """
        field_info = self._view['fields'].get(field_name)
        assert field_info is not None, f"{field_name!r} was not found in the view"
        assert field_info['type'] != 'one2many', "Can't set an one2many field directly, use its proxy instead"
        assert not self._get_modifier(field_name, 'readonly'), f"can't write on readonly field {field_name!r}"
        assert not self._get_modifier(field_name, 'invisible'), f"can't write on invisible field {field_name!r}"

        if field_info['type'] == 'many2many':
            return M2MProxy(self, field_name).set(value)

        if field_info['type'] == 'many2one':
            assert isinstance(value, BaseModel) and value._name == field_info['relation']
            value = value.id

        self._values[field_name] = value
        self._perform_onchange(field_name)