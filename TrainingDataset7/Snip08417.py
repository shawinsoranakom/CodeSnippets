def E006(name):
    return Error(
        "The {} setting must end with a slash.".format(name),
        id="urls.E006",
    )