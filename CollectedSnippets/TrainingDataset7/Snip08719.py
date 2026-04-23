def isatty(self):
        return hasattr(self._out, "isatty") and self._out.isatty()