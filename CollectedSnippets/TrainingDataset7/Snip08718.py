def flush(self):
        if hasattr(self._out, "flush"):
            self._out.flush()