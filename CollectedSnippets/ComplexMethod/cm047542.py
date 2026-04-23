def __init__(self, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if '__init__' in attrs and len(inspect.signature(attrs['__init__']).parameters) != 4:
            _logger.warning("The method %s.__init__ doesn't match the new signature in module %s", name, attrs.get('__module__'))

        if not attrs.get('_register', True):
            return

        # Remember which models to instantiate for this module.
        if self._module:
            self._module_to_models__[self._module].append(self)

        if not self._abstract and self._name not in self._inherit:
            # this class defines a model: add magic fields
            def add(name, field):
                setattr(self, name, field)
                field.__set_name__(self, name)

            def add_default(name, field):
                if name not in attrs:
                    setattr(self, name, field)
                    field.__set_name__(self, name)

            # make sure `id` field is still a `fields.Id`
            if not isinstance(self.id, Id):
                raise TypeError(f"Field {self.id} is not an instance of fields.Id")

            if attrs.get('_log_access', self._auto):
                from .fields_relational import Many2one  # noqa: PLC0415
                add_default('create_uid', Many2one(
                    'res.users', string='Created by', readonly=True))
                add_default('create_date', Datetime(
                    string='Created on', readonly=True))
                add_default('write_uid', Many2one(
                    'res.users', string='Last Updated by', readonly=True))
                add_default('write_date', Datetime(
                    string='Last Updated on', readonly=True))