def get_public_method(model: BaseModel, name: str):
    """ Get the public unbound method from a model.

    When the method does not exist or is inaccessible, raise appropriate errors.
    Accessible methods are public (in sense that python defined it:
    not prefixed with "_") and are not decorated with `@api.private`.
    """
    assert isinstance(model, BaseModel)
    e = f"Private methods (such as '{model._name}.{name}') cannot be called remotely."
    if name.startswith('_') or name in _UNSAFE_ATTRIBUTES:
        raise AccessError(e)

    cls = type(model)
    method = getattr(cls, name, None)
    if not callable(method):
        raise AttributeError(f"The method '{model._name}.{name}' does not exist")  # noqa: TRY004
    if method == getattr(model, name, None):  # classmethod, staticmethod
        e = f"The method '{model._name}.{name}' cannot be called remotely."
        raise AccessError(e)

    for mro_cls in cls.mro():
        if not (cla_method := getattr(mro_cls, name, None)):
            continue
        if getattr(cla_method, '_api_private', False):
            raise AccessError(e)

    return method