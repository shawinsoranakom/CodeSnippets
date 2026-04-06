def first_0flag(script_parts):
    return next((p for p in script_parts if len(p) == 2 and p.startswith("0")), None)