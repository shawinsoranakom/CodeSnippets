def set_attributes(self, params: dict) -> None:
        """Sets component attributes from the given parameters, preventing conflicts with reserved attribute names.

        Raises:
            ValueError: If a parameter name matches a reserved attribute not managed in _attributes and its
            value differs from the current attribute value.
        """
        self._validate_inputs(params)
        attributes = {}
        for key, value in params.items():
            if key in self.__dict__ and key not in self._attributes and value != getattr(self, key):
                msg = (
                    f"{self.__class__.__name__} defines an input parameter named '{key}' "
                    f"that is a reserved word and cannot be used."
                )
                raise ValueError(msg)
            attributes[key] = value
        for key, input_obj in self._inputs.items():
            if key not in attributes and key not in self._attributes:
                attributes[key] = input_obj.value or None

        self._attributes.update(attributes)