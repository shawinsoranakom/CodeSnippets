def _make_parser(self):
        """Create a hardened XML parser (no custom/external entities)."""
        return DefusedExpatParser()