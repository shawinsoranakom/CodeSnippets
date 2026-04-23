def replace(match: re.Match[str]) -> str:
            indent = match.group(1)
            key = match.group(2)
            comma_before = ""
            comma_after = ""
            if key[0] == "{":
                key = key[1:-1]
                if key[0] == ",":
                    comma_before = ", "
                    key = key[1:]
                if key[-1] == ",":
                    comma_after = ", "
                    key = key[:-1]
            v = lookup(key)
            if indent is not None:
                if not isinstance(v, list):
                    v = [v]
                return indent_lines(indent, v)
            elif isinstance(v, list):
                middle = ", ".join([str(x) for x in v])
                if len(v) == 0:
                    return middle
                return comma_before + middle + comma_after
            else:
                return str(v)