def config_specs(self) -> list[ConfigurableFieldSpec]:
        with _enums_for_spec_lock:
            if which_enum := _enums_for_spec.get(self.which):
                pass
            else:
                which_enum = StrEnum(  # type: ignore[call-overload]
                    self.which.name or self.which.id,
                    (
                        (v, v)
                        for v in [*list(self.alternatives.keys()), self.default_key]
                    ),
                )
                _enums_for_spec[self.which] = cast("type[StrEnum]", which_enum)
        return get_unique_config_specs(
            # which alternative
            [
                ConfigurableFieldSpec(
                    id=self.which.id,
                    name=self.which.name,
                    description=self.which.description,
                    annotation=which_enum,
                    default=self.default_key,
                    is_shared=self.which.is_shared,
                ),
            ]
            # config specs of the default option
            + (
                [
                    prefix_config_spec(s, f"{self.which.id}=={self.default_key}")
                    for s in self.default.config_specs
                ]
                if self.prefix_keys
                else self.default.config_specs
            )
            # config specs of the alternatives
            + [
                (
                    prefix_config_spec(s, f"{self.which.id}=={alt_key}")
                    if self.prefix_keys
                    else s
                )
                for alt_key, alt in self.alternatives.items()
                if isinstance(alt, RunnableSerializable)
                for s in alt.config_specs
            ]
        )