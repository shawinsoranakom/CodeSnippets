def solved(values):
    def unitsolved(unit):
        return {values[s] for s in unit} == set(digits)

    return values is not False and all(unitsolved(unit) for unit in unitlist)


def from_file(filename, sep="\n"):
    "Parse a file into a list of strings, separated by sep."
    with open(filename) as file:
        return file.read().strip().split(sep)
