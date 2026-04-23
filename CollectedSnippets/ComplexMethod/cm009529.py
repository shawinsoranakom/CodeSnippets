def get_name(self, suffix: str | None = None, *, name: str | None = None) -> str:
        """Get the name of the `Runnable`.

        Args:
            suffix: An optional suffix to append to the name.
            name: An optional name to use instead of the `Runnable`'s name.

        Returns:
            The name of the `Runnable`.
        """
        if name:
            name_ = name
        elif hasattr(self, "name") and self.name:
            name_ = self.name
        else:
            # Here we handle a case where the runnable subclass is also a pydantic
            # model.
            cls = self.__class__
            # Then it's a pydantic sub-class, and we have to check
            # whether it's a generic, and if so recover the original name.
            if (
                hasattr(
                    cls,
                    "__pydantic_generic_metadata__",
                )
                and "origin" in cls.__pydantic_generic_metadata__
                and cls.__pydantic_generic_metadata__["origin"] is not None
            ):
                name_ = cls.__pydantic_generic_metadata__["origin"].__name__
            else:
                name_ = cls.__name__

        if suffix:
            if name_[0].isupper():
                return name_ + suffix.title()
            return name_ + "_" + suffix.lower()
        return name_