def _setup_attrs__(self, model_class: type[BaseModel], name: str) -> None:
        """ Initialize the field parameter attributes. """
        attrs = self._get_attrs(model_class, name)

        # determine parameters that must be validated
        extra_keys = tuple(key for key in attrs if not hasattr(self, key))
        if extra_keys:
            attrs['_extra_keys__'] = extra_keys

        self.__dict__.update(attrs)

        # prefetch only stored, column, non-manual fields
        if not self.store or not self.column_type or self.manual:
            self.prefetch = False

        if not self.string and not self.related:
            # related fields get their string from their parent field
            self.string = (
                name[:-4] if name.endswith('_ids') else
                name[:-3] if name.endswith('_id') else name
            ).replace('_', ' ').title()

        # self.default must be either None or a callable
        if self.default is not None and not callable(self.default):
            value = self.default
            self.default = lambda model: value