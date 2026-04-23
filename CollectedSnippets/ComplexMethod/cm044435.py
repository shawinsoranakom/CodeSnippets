def get_serializer_from_filename(filename):
    """ Obtain a serializer object from a filename

    Parameters
    ----------
    filename: str
        Filename to determine the serializer type from

    Returns
    -------
    serializer: :class:`Serializer`
        A serializer object for handling the requested data format

    Example
    -------
    >>> filename = '/path/to/json/file.json'
    >>> serializer = get_serializer_from_filename(filename)
    """
    logger.debug("filename: '%s'", filename)
    extension = os.path.splitext(filename)[1].lower()
    logger.debug("extension: '%s'", extension)

    if extension == ".json":
        retval = _JSONSerializer()
    elif extension in (".p", ".pickle"):
        retval = _PickleSerializer()
    elif extension == ".npy":
        retval = _NPYSerializer()
    elif extension == ".fsa":
        retval = _CompressedSerializer()
    elif extension in (".yaml", ".yml") and _HAS_YAML:
        retval = _YAMLSerializer()
    elif extension in (".yaml", ".yml"):
        logger.warning("You must have PyYAML installed to use YAML as the serializer.\n"
                       "Switching to JSON as the serializer.")
        retval = _JSONSerializer()
    else:
        logger.warning("Unrecognized extension: '%s'. Returning json serializer", extension)
        retval = _JSONSerializer()
    logger.debug(retval)
    return retval