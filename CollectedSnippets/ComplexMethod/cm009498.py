def to_json(self) -> SerializedConstructor | SerializedNotImplemented:
        """Serialize the object to JSON.

        Raises:
            ValueError: If the class has deprecated attributes.

        Returns:
            A JSON serializable object or a `SerializedNotImplemented` object.
        """
        if not self.is_lc_serializable():
            return self.to_json_not_implemented()

        model_fields = type(self).model_fields
        secrets = {}
        # Get latest values for kwargs if there is an attribute with same name
        lc_kwargs = {}
        for k, v in self:
            if not _is_field_useful(self, k, v):
                continue
            # Do nothing if the field is excluded
            if k in model_fields and model_fields[k].exclude:
                continue

            lc_kwargs[k] = getattr(self, k, v)

        # Merge the lc_secrets and lc_attributes from every class in the MRO
        for cls in [None, *self.__class__.mro()]:
            # Once we get to Serializable, we're done
            if cls is Serializable:
                break

            if cls:
                deprecated_attributes = [
                    "lc_namespace",
                    "lc_serializable",
                ]

                for attr in deprecated_attributes:
                    if hasattr(cls, attr):
                        msg = (
                            f"Class {self.__class__} has a deprecated "
                            f"attribute {attr}. Please use the corresponding "
                            f"classmethod instead."
                        )
                        raise ValueError(msg)

            # Get a reference to self bound to each class in the MRO
            this = cast("Serializable", self if cls is None else super(cls, self))

            secrets.update(this.lc_secrets)
            # Now also add the aliases for the secrets
            # This ensures known secret aliases are hidden.
            # Note: this does NOT hide any other extra kwargs
            # that are not present in the fields.
            for key in list(secrets):
                value = secrets[key]
                if (key in model_fields) and (
                    alias := model_fields[key].alias
                ) is not None:
                    secrets[alias] = value
            lc_kwargs.update(this.lc_attributes)

        # include all secrets, even if not specified in kwargs
        # as these secrets may be passed as an environment variable instead
        for key in secrets:
            secret_value = getattr(self, key, None) or lc_kwargs.get(key)
            if secret_value is not None:
                lc_kwargs.update({key: secret_value})

        return {
            "lc": 1,
            "type": "constructor",
            "id": self.lc_id(),
            "kwargs": lc_kwargs
            if not secrets
            else _replace_secrets(lc_kwargs, secrets),
        }