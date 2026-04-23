def _normalise_transformer_value(value: Maybe[str | list[Any]]) -> Maybe[list[Any]]:
        # To simplify downstream logics, reduce the type options to array of transformations.
        # TODO: add further validation logic
        # TODO: should we sort to avoid detecting user-side ordering changes as template changes?
        if isinstance(value, NothingType):
            return value
        elif isinstance(value, str):
            value = [NormalisedGlobalTransformDefinition(Name=value, Parameters=Nothing)]
        elif isinstance(value, list):
            tmp_value = []
            for item in value:
                if isinstance(item, str):
                    tmp_value.append(
                        NormalisedGlobalTransformDefinition(Name=item, Parameters=Nothing)
                    )
                else:
                    tmp_value.append(item)
            value = tmp_value
        elif isinstance(value, dict):
            if "Name" not in value:
                raise RuntimeError(f"Missing 'Name' field in Transform definition '{value}'")
            name = value["Name"]
            parameters = value.get("Parameters", Nothing)
            value = [NormalisedGlobalTransformDefinition(Name=name, Parameters=parameters)]
        else:
            raise RuntimeError(f"Invalid Transform definition: '{value}'")
        return value