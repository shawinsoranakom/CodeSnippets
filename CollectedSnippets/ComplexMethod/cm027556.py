def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[Any, Any],
        **kwargs: Any,
    ) -> None:
        """Optionally create a dataclass and store it in cls._dataclass.

        A dataclass will be created if frozen_or_thawed is set, if not we assume the
        class will be a real dataclass, i.e. it's decorated with @dataclass.
        """
        if not namespace["_FrozenOrThawed__frozen_or_thawed"]:
            # This class is a real dataclass, optionally inject the parent's annotations
            if all(dataclasses.is_dataclass(base) for base in bases):
                # All direct parents are dataclasses, rely on dataclass inheritance
                return
            # Parent is not a dataclass, inject all parents' annotations
            annotations: dict[str, Any] = {}
            for parent in cls.__mro__[::-1]:
                if parent is object:
                    continue
                annotations |= get_annotations(parent, format=Format.FORWARDREF)

            if "__annotations__" in cls.__dict__:
                cls.__annotations__ = annotations
            else:

                def wrapped_annotate(format: Format) -> dict[str, Any]:
                    # Note: to avoid complicating things, we only support FORWARDREF
                    return annotations

                cls.__annotate__ = wrapped_annotate
            return

        # First try without setting the kw_only flag, and if that fails, try setting it
        try:
            cls._make_dataclass(name, bases, False)
        except TypeError:
            cls._make_dataclass(name, bases, True)

        def __new__(*args: Any, **kwargs: Any) -> object:
            """Create a new instance.

            The function has no named arguments to avoid name collisions with dataclass
            field names.
            """
            cls, *_args = args
            if dataclasses.is_dataclass(cls):
                if TYPE_CHECKING:
                    cls = cast(type[DataclassInstance], cls)
                return object.__new__(cls)
            return cls._dataclass(*_args, **kwargs)

        cls.__init__ = cls._dataclass.__init__  # type: ignore[misc]
        cls.__new__ = __new__