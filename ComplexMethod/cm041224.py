def _resource_name_transformer(key: str, val: str) -> str:
    if isinstance(val, str):
        match = re.match(PATTERN_ARN, val)
        if match:
            res = match.groups()[-1]
            if res.startswith("<") and res.endswith(">"):
                # value was already replaced
                # TODO: this isn't enforced or unfortunately even upheld via standard right now
                return None
            if ":changeSet/" in val:
                return val.split(":changeSet/")[-1]
            if "/" in res:
                return res.split("/")[-1]
            if res.startswith("function:"):
                res = res.replace("function:", "")
                if "$" in res:
                    res = res.split("$")[0].rstrip(":")
                return res
            if res.startswith("layer:"):
                # extract layer name from arn
                match res.split(":"):
                    case _, layer_name, _:  # noqa
                        return layer_name  # noqa
                    case _, layer_name:  # noqa
                        return layer_name  # noqa
            if ":" in res:
                return res.split(":")[-1]  # TODO might not work for every replacement
            return res
        return None