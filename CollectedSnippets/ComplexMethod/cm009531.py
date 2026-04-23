def OutputType(self) -> type[Output]:  # noqa: N802
        """Output Type.

        The type of output this `Runnable` produces specified as a type annotation.

        Raises:
            TypeError: If the output type cannot be inferred.
        """
        # First loop through bases -- this will help generic
        # any pydantic models.
        for base in self.__class__.mro():
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                if (
                    "args" in metadata
                    and len(metadata["args"]) == _RUNNABLE_GENERIC_NUM_ARGS
                ):
                    return cast("type[Output]", metadata["args"][1])

        for cls in self.__class__.__orig_bases__:  # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == _RUNNABLE_GENERIC_NUM_ARGS:
                return cast("type[Output]", type_args[1])

        msg = (
            f"Runnable {self.get_name()} doesn't have an inferable OutputType. "
            "Override the OutputType property to specify the output type."
        )
        raise TypeError(msg)