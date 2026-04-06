def __post_init__(self) -> None:
        with warnings.catch_warnings():
            # Pydantic >= 2.12.0 warns about field specific metadata that is unused
            # (e.g. `TypeAdapter(Annotated[int, Field(alias='b')])`). In some cases, we
            # end up building the type adapter from a model field annotation so we
            # need to ignore the warning:
            if shared.PYDANTIC_VERSION_MINOR_TUPLE >= (2, 12):
                from pydantic.warnings import UnsupportedFieldAttributeWarning

                warnings.simplefilter(
                    "ignore", category=UnsupportedFieldAttributeWarning
                )
            # TODO: remove after setting the min Pydantic to v2.12.3
            # that adds asdict(), and use self.field_info.asdict() instead
            field_dict = asdict(self.field_info)
            annotated_args = (
                field_dict["annotation"],
                *field_dict["metadata"],
                # this FieldInfo needs to be created again so that it doesn't include
                # the old field info metadata and only the rest of the attributes
                Field(**field_dict["attributes"]),
            )
            self._type_adapter: TypeAdapter[Any] = TypeAdapter(
                Annotated[annotated_args],  # ty: ignore[invalid-type-form]
                config=self.config,
            )