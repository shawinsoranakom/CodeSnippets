def __repr__(self) -> str:
        """Return a string representation of this `Runnable`."""
        if self._repr is None:
            if hasattr(self, "func") and isinstance(self.func, itemgetter):
                self._repr = f"RunnableLambda({str(self.func)[len('operator.') :]})"
            elif hasattr(self, "func"):
                self._repr = f"RunnableLambda({get_lambda_source(self.func) or '...'})"
            elif hasattr(self, "afunc"):
                self._repr = (
                    f"RunnableLambda(afunc={get_lambda_source(self.afunc) or '...'})"
                )
            else:
                self._repr = "RunnableLambda(...)"
        return self._repr