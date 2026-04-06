def _get_suggestions(str):
    suggestions = str.replace(" or ", ", ").split(", ")
    return suggestions