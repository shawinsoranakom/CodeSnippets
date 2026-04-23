def _read_patchlevel_version(sources):
    if not sources.match("Include"):
        sources /= "Include"
    values = {}
    with open(sources / "patchlevel.h", "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'#\s*define\s+(PY_\S+?)\s+(\S+)', line.strip(), re.I)
            if m and m.group(2):
                v = m.group(2)
                if v.startswith('"'):
                    v = v[1:-1]
                else:
                    v = values.get(v, v)
                    if isinstance(v, str):
                        try:
                            v = int(v, 16 if v.startswith("0x") else 10)
                        except ValueError:
                            pass
                values[m.group(1)] = v
    return (
        values["PY_MAJOR_VERSION"],
        values["PY_MINOR_VERSION"],
        values["PY_MICRO_VERSION"],
        values["PY_RELEASE_LEVEL"] << 4 | values["PY_RELEASE_SERIAL"],
    )