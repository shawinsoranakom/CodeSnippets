def select_by(dictlist, key, value):
    return [x for x in dictlist if x[key] == value][0]