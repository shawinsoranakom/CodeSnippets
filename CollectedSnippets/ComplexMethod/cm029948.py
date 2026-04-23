def describe(thing):
    """Produce a short description of the given thing."""
    if inspect.ismodule(thing):
        if thing.__name__ in sys.builtin_module_names:
            return 'built-in module ' + thing.__name__
        if hasattr(thing, '__path__'):
            return 'package ' + thing.__name__
        else:
            return 'module ' + thing.__name__
    if inspect.isbuiltin(thing):
        return 'built-in function ' + thing.__name__
    if inspect.isgetsetdescriptor(thing):
        return 'getset descriptor %s.%s.%s' % (
            thing.__objclass__.__module__, thing.__objclass__.__name__,
            thing.__name__)
    if inspect.ismemberdescriptor(thing):
        return 'member descriptor %s.%s.%s' % (
            thing.__objclass__.__module__, thing.__objclass__.__name__,
            thing.__name__)
    if inspect.isclass(thing):
        return 'class ' + thing.__name__
    if inspect.isfunction(thing):
        return 'function ' + thing.__name__
    if inspect.ismethod(thing):
        return 'method ' + thing.__name__
    if inspect.ismethodwrapper(thing):
        return 'method wrapper ' + thing.__name__
    if inspect.ismethoddescriptor(thing):
        try:
            return 'method descriptor ' + thing.__name__
        except AttributeError:
            pass
    return type(thing).__name__