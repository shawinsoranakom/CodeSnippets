def deconstruct(self):
        kwargs = {"name": self.name, "locale": self.locale}
        if self.provider and self.provider != "libc":
            kwargs["provider"] = self.provider
        if self.deterministic is False:
            kwargs["deterministic"] = self.deterministic
        return (
            self.__class__.__qualname__,
            [],
            kwargs,
        )