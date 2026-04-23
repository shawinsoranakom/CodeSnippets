def parameterized_class(attrs, input_list=None):
  if isinstance(attrs, list) and (not attrs or isinstance(attrs[0], dict)):
    params_list = attrs
  else:
    assert input_list is not None
    attr_names = (attrs,) if isinstance(attrs, str) else tuple(attrs)
    params_list = [dict(zip(attr_names, v if isinstance(v, (tuple, list)) else (v,), strict=False)) for v in input_list]

  def decorator(cls):
    globs = sys._getframe(1).f_globals
    for i, params in enumerate(params_list):
      name = f"{cls.__name__}_{i}"
      new_cls = type(name, (cls,), dict(params))
      new_cls.__module__ = cls.__module__
      new_cls.__test__ = True  # override inherited False so pytest collects this subclass
      globs[name] = new_cls
    # Don't collect the un-parametrised base, but return it so outer decorators
    # (e.g. @pytest.mark.skip) land on it and propagate to subclasses via MRO.
    cls.__test__ = False
    return cls

  return decorator