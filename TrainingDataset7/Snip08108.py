def check(self, **kwargs):
        raise NotImplementedError(
            "subclasses may provide a check() method to verify the finder is "
            "configured correctly."
        )