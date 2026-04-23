def get_serializer(serializer):
    """ Obtain a serializer object

    Parameters
    ----------
    serializer: {'json', 'pickle', yaml', 'npy', 'compressed'}
        The required serializer format

    Returns
    -------
    serializer: :class:`Serializer`
        A serializer object for handling the requested data format

    Example
    -------
    >>> serializer = get_serializer('json')
    """
    retval = None
    if serializer.lower() == "npy":
        retval = _NPYSerializer()
    elif serializer.lower() == "compressed":
        retval = _CompressedSerializer()
    elif serializer.lower() == "json":
        retval = _JSONSerializer()
    elif serializer.lower() == "pickle":
        retval = _PickleSerializer()
    elif serializer.lower() == "yaml" and _HAS_YAML:
        retval = _YAMLSerializer()
    elif serializer.lower() == "yaml":
        logger.warning("You must have PyYAML installed to use YAML as the serializer."
                       "Switching to JSON as the serializer.")
        retval = _JSONSerializer
    else:
        logger.warning("Unrecognized serializer: '%s'. Returning json serializer", serializer)
    logger.debug(retval)
    return retval