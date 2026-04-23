def random(value):
    """Return a random item from the list."""
    try:
        return random_module.choice(value)
    except IndexError:
        return ""