def InputType(self) -> type[Input]:  # noqa: N802
        """Input type.

        The type of input this `Runnable` accepts specified as a type annotation.

        Raises:
            TypeError: If the input type cannot be inferred.
        """
        # First loop through all parent classes and if any of them is
        # a Pydantic model, we will pick up the generic parameterization
        # from that model via the __pydantic_generic_metadata__ attribute.
        for base in self.__class__.mro():
            if hasattr(base, "__pydantic_generic_metadata__"):
                metadata = base.__pydantic_generic_metadata__
                if (
                    "args" in metadata
                    and len(metadata["args"]) == _RUNNABLE_GENERIC_NUM_ARGS
                ):
                    return cast("type[Input]", metadata["args"][0])

        # If we didn't find a Pydantic model in the parent classes,
        # then loop through __orig_bases__. This corresponds to
        # Runnables that are not pydantic models.
        for cls in self.__class__.__orig_bases__:  # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == _RUNNABLE_GENERIC_NUM_ARGS:
                return cast("type[Input]", type_args[0])

        msg = (
            f"Runnable {self.get_name()} doesn't have an inferable InputType. "
            "Override the InputType property to specify the input type."
        )
        raise TypeError(msg)