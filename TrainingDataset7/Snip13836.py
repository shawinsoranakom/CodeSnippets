def is_pickable(obj):
    """
    Returns true if the object can be dumped and loaded through the pickle
    module.
    """
    try:
        pickle.loads(pickle.dumps(obj))
    except (AttributeError, TypeError, pickle.PickleError):
        return False
    return True