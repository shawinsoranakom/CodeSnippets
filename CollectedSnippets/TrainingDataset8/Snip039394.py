def get_byte_length(value):
    """Return the byte length of the pickled value."""
    return len(pickle.dumps(value))