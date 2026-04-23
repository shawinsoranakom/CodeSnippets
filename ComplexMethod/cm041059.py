def _visit(obj, path, **_):
        # Fn::ForEach
        # TODO: can this be used in non-resource positions?
        if isinstance(obj, dict) and any("Fn::ForEach" in key for key in obj):
            newobj = {}
            for key in obj:
                if "Fn::ForEach" not in key:
                    newobj[key] = obj[key]
                    continue

                new_entries = expand_fn_foreach(obj[key], resolve_context)
                newobj.update(**new_entries)
            return newobj
        # Fn::Length
        elif isinstance(obj, dict) and "Fn::Length" in obj:
            value = obj["Fn::Length"]
            if isinstance(value, dict):
                value = resolve_context.resolve(value)

            if isinstance(value, list):
                # TODO: what if one of the elements was AWS::NoValue?
                # no conversion required
                return len(value)
            elif isinstance(value, str):
                length = len(value.split(","))
                return length
            return obj
        elif isinstance(obj, dict) and "Fn::ToJsonString" in obj:
            # TODO: is the default representation ok here?
            return json.dumps(obj["Fn::ToJsonString"], default=str, separators=(",", ":"))

            # reference
        return obj