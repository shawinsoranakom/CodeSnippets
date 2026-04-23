def __new__(meta, name, bases, attrs):
        # this prevents assignment of non-fields on recordsets
        attrs.setdefault('__slots__', ())
        # this collects the fields defined on the class (via Field.__set_name__())
        attrs.setdefault('_field_definitions', [])
        # this collects the table object definitions on the class (via TableObject.__set_name__())
        attrs.setdefault('_table_object_definitions', [])

        if attrs.get('_register', True):
            # determine '_module'
            if '_module' not in attrs:
                module = attrs['__module__']
                assert module.startswith('odoo.addons.'), \
                    f"Invalid import of {module}.{name}, it should start with 'odoo.addons'."
                attrs['_module'] = module.split('.')[2]

            _inherit = attrs.get('_inherit')
            if _inherit and isinstance(_inherit, str):
                attrs.setdefault('_name', _inherit)
                attrs['_inherit'] = [_inherit]

            if not attrs.get('_name'):
                # add '.' before every uppercase letter preceded by any non-underscore char
                attrs['_name'] = re.sub(r"(?<=[^_])([A-Z])", r".\1", name).lower()
                _logger.warning("Class %s has no _name, please make it explicit: _name = %r", name, attrs['_name'])

            assert attrs.get('_name')

        return super().__new__(meta, name, bases, attrs)