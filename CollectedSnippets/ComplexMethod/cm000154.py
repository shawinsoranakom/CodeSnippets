def _plugboard(pbstring: str) -> dict[str, str]:
    """
    https://en.wikipedia.org/wiki/Enigma_machine#Plugboard

    >>> _plugboard('PICTURES')
    {'P': 'I', 'I': 'P', 'C': 'T', 'T': 'C', 'U': 'R', 'R': 'U', 'E': 'S', 'S': 'E'}
    >>> _plugboard('POLAND')
    {'P': 'O', 'O': 'P', 'L': 'A', 'A': 'L', 'N': 'D', 'D': 'N'}

    In the code, ``pb`` stands for ``plugboard``

    Pairs can be separated by spaces

    :param pbstring: string containing plugboard setting for the Enigma machine
    :return: dictionary containing converted pairs
    """

    # tests the input string if it
    # a) is type string
    # b) has even length (so pairs can be made)
    if not isinstance(pbstring, str):
        msg = f"Plugboard setting isn't type string ({type(pbstring)})"
        raise TypeError(msg)
    elif len(pbstring) % 2 != 0:
        msg = f"Odd number of symbols ({len(pbstring)})"
        raise Exception(msg)
    elif pbstring == "":
        return {}

    pbstring.replace(" ", "")

    # Checks if all characters are unique
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

    # Created the dictionary
    pb = {}
    for j in range(0, len(pbstring) - 1, 2):
        pb[pbstring[j]] = pbstring[j + 1]
        pb[pbstring[j + 1]] = pbstring[j]

    return pb