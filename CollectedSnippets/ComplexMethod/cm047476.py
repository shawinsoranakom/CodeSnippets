def setup_related(self, model: BaseModel) -> None:
        """ Setup the attributes of a related field. """
        assert isinstance(self.related, str), self.related

        # determine the chain of fields, and make sure they are all set up
        field_seq = []
        model_name = self.model_name
        for name in self.related.split('.'):
            field = model.pool[model_name]._fields.get(name)
            if field is None:
                raise KeyError(
                    f"Field {name} referenced in related field definition {self} does not exist."
                )
            if not field._setup_done:
                field.setup(model.env[model_name])
            field_seq.append(field)
            model_name = field.comodel_name

        # check type consistency
        if self.type != field.type:
            raise TypeError("Type of related field %s is inconsistent with %s" % (self, field))

        self.related_field = field

        # if field's setup is invalidated, then self's setup must be invalidated, too
        model.pool.field_setup_dependents.add(field, self)

        # determine dependencies, compute, inverse, and search
        self.compute = self._compute_related
        if self.inherited or not (self.readonly or field.readonly):
            self.inverse = self._inverse_related
        if not self.store and all(f._description_searchable for f in field_seq):
            # allow searching on self only if the related field is searchable
            self.search = self._search_related

        # A readonly related field without an inverse method should not have a
        # default value, as it does not make sense.
        if self.default and self.readonly and not self.inverse:
            _logger.warning("Redundant default on %s", self)

        # copy attributes from field to self (string, help, etc.)
        for attr, prop in self.related_attrs:
            # check whether 'attr' is explicitly set on self (from its field
            # definition), and ignore its class-level value (only a default)
            if attr not in self.__dict__ and prop.startswith('_related_'):
                setattr(self, attr, getattr(field, prop))

        for attr in field._extra_keys__:
            if not hasattr(self, attr) and model._valid_field_parameter(self, attr):
                setattr(self, attr, getattr(field, attr))

        # special cases of inherited fields
        if self.inherited:
            self.inherited_field = field
            if field.required:
                self.required = True
            # add modules from delegate and target fields; the first one ensures
            # that inherited fields introduced via an abstract model (_inherits
            # being on the abstract model) are assigned an XML id
            delegate_field = model._fields[self.related.split('.')[0]]
            self._modules = tuple({*self._modules, *delegate_field._modules, *field._modules})