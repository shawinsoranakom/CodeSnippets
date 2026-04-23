def __init__(self, prec=None, rounding=None, Emin=None, Emax=None,
                       capitals=None, clamp=None, flags=None, traps=None,
                       _ignored_flags=None):
        # Set defaults; for everything except flags and _ignored_flags,
        # inherit from DefaultContext.
        try:
            dc = DefaultContext
        except NameError:
            pass

        self.prec = prec if prec is not None else dc.prec
        self.rounding = rounding if rounding is not None else dc.rounding
        self.Emin = Emin if Emin is not None else dc.Emin
        self.Emax = Emax if Emax is not None else dc.Emax
        self.capitals = capitals if capitals is not None else dc.capitals
        self.clamp = clamp if clamp is not None else dc.clamp

        if _ignored_flags is None:
            self._ignored_flags = []
        else:
            self._ignored_flags = _ignored_flags

        if traps is None:
            self.traps = dc.traps.copy()
        elif not isinstance(traps, dict):
            self.traps = dict((s, int(s in traps)) for s in _signals + traps)
        else:
            self.traps = traps

        if flags is None:
            self.flags = dict.fromkeys(_signals, 0)
        elif not isinstance(flags, dict):
            self.flags = dict((s, int(s in flags)) for s in _signals + flags)
        else:
            self.flags = flags