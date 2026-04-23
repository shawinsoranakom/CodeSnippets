def __init__(self, *args, _connector=None, _negated=False, **kwargs):
        if _connector not in self.connectors:
            connector_reprs = ", ".join(f"{conn!r}" for conn in self.connectors[1:])
            raise ValueError(f"_connector must be one of {connector_reprs}, or None.")
        super().__init__(
            children=[*args, *sorted(kwargs.items())],
            connector=_connector,
            negated=_negated,
        )