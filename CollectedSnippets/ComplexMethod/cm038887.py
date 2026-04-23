def parse_client_command(cmd: str) -> dict[str, Any]:
    """Parse the client_command shell string into {executable, script, args}."""
    toks = shlex.split(cmd)
    if len(toks) < 2:
        raise ValueError("client_command must include an executable and a script")
    executable, script = toks[0], toks[1]
    args: dict[str, Any] = {}

    i = 2
    while i < len(toks):
        t = toks[i]
        if t.startswith("--"):
            # --key=value or --key (value) or boolean flag
            if "=" in t:
                key, val = t.split("=", 1)
                if key == "--metadata":
                    md = {}
                    if val:
                        if "=" in val:
                            k, v = val.split("=", 1)
                            md[k] = _coerce(v)
                        else:
                            md[val] = True
                    args[key] = md
                else:
                    args[key] = _coerce(val)
                i += 1
                continue

            key = t

            # Special: consume metadata k=v pairs until next --flag
            if key == "--metadata":
                i += 1
                md = {}
                while i < len(toks) and not toks[i].startswith("--"):
                    pair = toks[i]
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        md[k] = _coerce(v)
                    else:
                        md[pair] = True
                    i += 1
                args[key] = md
                continue

            # Standard: check if next token is a value (not a flag)
            if i + 1 < len(toks) and not toks[i + 1].startswith("--"):
                args[key] = _coerce(toks[i + 1])
                i += 2
            else:
                # lone flag -> True
                args[key] = True
                i += 1
        else:
            # unexpected positional; skip
            i += 1

    return {"executable": executable, "script": script, "args": args}