def dump_component(self) -> ComponentModel:
        """Dump the component to a model that can be loaded back in.

        Raises:
            TypeError: If the component is a local class.

        Returns:
            ComponentModel: The model representing the component.
        """
        if self.component_provider_override is not None:
            provider = self.component_provider_override
        else:
            provider = _type_to_provider_str(self.__class__)
            # Warn if internal module name is used,
            if "._" in provider:
                warnings.warn(
                    "Internal module name used in provider string. This is not recommended and may cause issues in the future. Silence this warning by setting component_provider_override to this value.",
                    stacklevel=2,
                )

        if "<locals>" in provider:
            raise TypeError("Cannot dump component with local class")

        if not hasattr(self, "component_type"):
            raise AttributeError("component_type not defined")

        description = self.component_description
        if description is None and self.__class__.__doc__:
            # use docstring as description
            docstring = self.__class__.__doc__.strip()
            for marker in ["\n\nArgs:", "\n\nParameters:", "\n\nAttributes:", "\n\n"]:
                docstring = docstring.split(marker)[0]
            description = docstring.strip()

        obj_config = self._to_config().model_dump(exclude_none=True)
        model = ComponentModel(
            provider=provider,
            component_type=self.component_type,
            version=self.component_version,
            component_version=self.component_version,
            description=description,
            label=self.component_label or self.__class__.__name__,
            config=obj_config,
        )
        return model