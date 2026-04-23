def import_library(name):
    """
    Load a Library object from a template tag module.
    """
    try:
        module = import_module(name)
    except ImportError as e:
        raise InvalidTemplateLibrary(
            "Invalid template library specified. ImportError raised when "
            "trying to load '%s': %s" % (name, e)
        )
    try:
        return module.register
    except AttributeError:
        raise InvalidTemplateLibrary(
            "Module %s does not have a variable named 'register'" % name,
        )