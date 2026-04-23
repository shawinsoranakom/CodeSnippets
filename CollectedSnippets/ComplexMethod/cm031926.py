def __init__(self, item, typedecl=None, *, unsupported=None, **extra):
        if 'unsupported' in extra:
            raise NotImplementedError((item, typedecl, unsupported, extra))
        if not unsupported:
            unsupported = None
        elif isinstance(unsupported, (str, TypeDeclaration)):
            unsupported = (unsupported,)
        elif unsupported is not FIXED_TYPE:
            unsupported = tuple(unsupported)
        self.unsupported = unsupported
        extra['unsupported'] = self.unsupported  # ...for __repr__(), etc.
        if self.unsupported is None:
            #self.supported = None
            self.supported = True
        elif self.unsupported is FIXED_TYPE:
            if item.kind is KIND.VARIABLE:
                raise NotImplementedError(item, typedecl, unsupported)
            self.supported = True
        else:
            self.supported = not self.unsupported
        super().__init__(item, typedecl, **extra)