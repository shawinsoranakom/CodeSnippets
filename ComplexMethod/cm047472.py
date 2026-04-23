def __set_name__(self, owner: type[BaseModel], name: str) -> None:
        """ Perform the base setup of a field.

        :param owner: the owner class of the field (the model's definition or registry class)
        :param name: the name of the field
        """
        # during initialization, when importing `_models` at the end of this
        # file, it is not yet available and we already declare fields:
        # id and display_name
        assert '_models' not in globals() or isinstance(owner, _models.MetaModel)
        self.model_name = owner._name
        self.name = name
        if getattr(owner, 'pool', None) is None:  # models.is_model_definition(owner)
            # only for fields on definition classes, not registry classes
            self._module = owner._module
            owner._field_definitions.append(self)

        if not self._args__.get('related'):
            self._direct = True
        if self._direct or self._toplevel:
            self._setup_attrs__(owner, name)
            if self._toplevel:
                # free memory from stuff that is no longer useful
                self.__dict__.pop('_args__', None)
                if not self.related:
                    # keep _base_fields__ on related fields for incremental model setup
                    self.__dict__.pop('_base_fields__', None)