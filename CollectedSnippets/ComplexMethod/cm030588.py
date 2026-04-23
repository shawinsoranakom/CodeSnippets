def __init__(self, prec=None, rounding=None, Emin=None, Emax=None,
                               capitals=None, clamp=None, flags=None,
                               traps=None):
                Context.__init__(self)
                if prec is not None:
                    self.prec = prec
                if rounding is not None:
                    self.rounding = rounding
                if Emin is not None:
                    self.Emin = Emin
                if Emax is not None:
                    self.Emax = Emax
                if capitals is not None:
                    self.capitals = capitals
                if clamp is not None:
                    self.clamp = clamp
                if flags is not None:
                    if isinstance(flags, list):
                        flags = {v:(v in flags) for v in OrderedSignals[decimal] + flags}
                    self.flags = flags
                if traps is not None:
                    if isinstance(traps, list):
                        traps = {v:(v in traps) for v in OrderedSignals[decimal] + traps}
                    self.traps = traps