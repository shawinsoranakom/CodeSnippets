def from_field(cls, type_hints: dict[str, t.Any], metadata: FieldSettings, dc_field: dataclasses.Field) -> t.Self:
        resolved_type = type_hints[dc_field.name]

        if isinstance(resolved_type, types.UnionType):
            args = resolved_type.__args__

            if len(args) == 2 and args[0] is types.NoneType:
                resolved_type = args[1]
                optional = True
            elif len(args) == 2 and args[1] is types.NoneType:
                resolved_type = args[0]
                optional = True
            else:
                raise NotImplementedError(f"Unexpected union type args: {args}")
        else:
            optional = False

        if isinstance(resolved_type, types.GenericAlias):
            resolved_type = t.get_origin(resolved_type)
        elif (orig_bases := types.get_original_bases(resolved_type)) and orig_bases[0] is t.TypedDict:
            resolved_type = dict

        return cls(
            name=dc_field.name,
            type=resolved_type,
            optional=optional,
            field=dc_field,
            metadata=metadata,
        )