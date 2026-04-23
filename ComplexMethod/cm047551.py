def _add_missing_default_values(self, values: ValuesType) -> ValuesType:
        # avoid overriding inherited values when parent is set
        avoid_models = set()

        def collect_models_to_avoid(model):
            for parent_mname, parent_fname in model._inherits.items():
                if parent_fname in values:
                    avoid_models.add(parent_mname)
                else:
                    # manage the case where an ancestor parent field is set
                    collect_models_to_avoid(self.env[parent_mname])

        collect_models_to_avoid(self)

        def avoid(field):
            # check whether the field is inherited from one of avoid_models
            if avoid_models:
                while field.inherited:
                    field = field.related_field
                    if field.model_name in avoid_models:
                        return True
            return False

        # compute missing fields
        missing_defaults = [
            name
            for name, field in self._fields.items()
            if name not in values
            if not avoid(field)
        ]

        if missing_defaults:
            # override defaults with the provided values, never allow the other way around
            defaults = self.default_get(missing_defaults)
            for name, value in defaults.items():
                if self._fields[name].type == 'many2many' and value and isinstance(value[0], int):
                    # convert a list of ids into a list of commands
                    defaults[name] = [Command.set(value)]
                elif self._fields[name].type == 'one2many' and value and isinstance(value[0], dict):
                    # convert a list of dicts into a list of commands
                    defaults[name] = [Command.create(x) for x in value]
            defaults.update(values)

        else:
            defaults = values

        # delegate the default properties to the properties field
        for field in self._fields.values():
            if field.type == 'properties':
                defaults[field.name] = field._add_default_values(self.env, defaults)

        return defaults