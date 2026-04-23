def render_doc(thing, title='Python Library Documentation: %s', forceload=0,
        renderer=None):
    """Render text documentation, given an object or a path to an object."""
    if renderer is None:
        renderer = text
    object, name = resolve(thing, forceload)
    desc = describe(object)
    module = inspect.getmodule(object)
    if name and '.' in name:
        desc += ' in ' + name[:name.rfind('.')]
    elif module and module is not object:
        desc += ' in module ' + module.__name__

    if not (inspect.ismodule(object) or
              inspect.isclass(object) or
              inspect.isroutine(object) or
              inspect.isdatadescriptor(object) or
              _getdoc(object)):
        # If the passed object is a piece of data or an instance,
        # document its available methods instead of its value.
        if hasattr(object, '__origin__'):
            object = object.__origin__
        else:
            object = type(object)
            desc += ' object'
    return title % desc + '\n\n' + renderer.document(object, name)