def _generic_init_subclass(cls, *args, **kwargs):
    super(Generic, cls).__init_subclass__(*args, **kwargs)
    tvars = []
    if '__orig_bases__' in cls.__dict__:
        error = Generic in cls.__orig_bases__
    else:
        error = (Generic in cls.__bases__ and
                    cls.__name__ != 'Protocol' and
                    type(cls) != _TypedDictMeta)
    if error:
        raise TypeError("Cannot inherit from plain Generic")
    if '__orig_bases__' in cls.__dict__:
        tvars = _collect_type_parameters(cls.__orig_bases__, validate_all=True)
        # Look for Generic[T1, ..., Tn].
        # If found, tvars must be a subset of it.
        # If not found, tvars is it.
        # Also check for and reject plain Generic,
        # and reject multiple Generic[...].
        gvars = None
        basename = None
        for base in cls.__orig_bases__:
            if (isinstance(base, _GenericAlias) and
                    base.__origin__ in (Generic, Protocol)):
                if gvars is not None:
                    raise TypeError(
                        "Cannot inherit from Generic[...] multiple times.")
                gvars = base.__parameters__
                basename = base.__origin__.__name__
        if gvars is not None:
            tvarset = set(tvars)
            gvarset = set(gvars)
            if not tvarset <= gvarset:
                s_vars = ', '.join(str(t) for t in tvars if t not in gvarset)
                s_args = ', '.join(str(g) for g in gvars)
                raise TypeError(f"Some type variables ({s_vars}) are"
                                f" not listed in {basename}[{s_args}]")
            tvars = gvars
    cls.__parameters__ = tuple(tvars)