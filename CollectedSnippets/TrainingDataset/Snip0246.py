def _plugboard(pbstring: str) -> dict[str, str]:

    if not isinstance(pbstring, str):
        msg = f"Plugboard setting isn't type string ({type(pbstring)})"
        raise TypeError(msg)
    elif len(pbstring) % 2 != 0:
        msg = f"Odd number of symbols ({len(pbstring)})"
        raise Exception(msg)
    elif pbstring == "":
        return {}

    pbstring.replace(" ", "")

    tmppbl = set()
    for i in pbstring:
        if i not in abc:
            msg = f"'{i}' not in list of symbols"
            raise Exception(msg)
        elif i in tmppbl:
            msg = f"Duplicate symbol ({i})"
            raise Exception(msg)
        else:
            tmppbl.add(i)
    del tmppbl

    pb = {}
    for j in range(0, len(pbstring) - 1, 2):
        pb[pbstring[j]] = pbstring[j + 1]
        pb[pbstring[j + 1]] = pbstring[j]

    return pb
