def strconvert(d):
    "Converts all keys in dictionary to str type."
    return {str(k): v for k, v in d.items()}