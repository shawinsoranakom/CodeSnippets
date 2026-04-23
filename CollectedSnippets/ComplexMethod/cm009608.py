def deprecate(
        obj: T,
        *,
        _obj_type: str = obj_type,
        _name: str = name,
        _message: str = message,
        _alternative: str = alternative,
        _alternative_import: str = alternative_import,
        _pending: bool = pending,
        _addendum: str = addendum,
        _package: str = package,
    ) -> T:
        """Implementation of the decorator returned by `deprecated`."""

        def emit_warning() -> None:
            """Emit the warning."""
            warn_deprecated(
                since,
                message=_message,
                name=_name,
                alternative=_alternative,
                alternative_import=_alternative_import,
                pending=_pending,
                obj_type=_obj_type,
                addendum=_addendum,
                removal=removal,
                package=_package,
            )

        warned = False

        def warning_emitting_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the original wrapped callable that emits a warning.

            Args:
                *args: The positional arguments to the function.
                **kwargs: The keyword arguments to the function.

            Returns:
                The return value of the function being wrapped.
            """
            nonlocal warned
            if not warned and not is_caller_internal():
                warned = True
                emit_warning()
            return wrapped(*args, **kwargs)

        async def awarning_emitting_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Same as warning_emitting_wrapper, but for async functions."""
            nonlocal warned
            if not warned and not is_caller_internal():
                warned = True
                emit_warning()
            return await wrapped(*args, **kwargs)

        _package = _package or obj.__module__.split(".")[0].replace("_", "-")

        if isinstance(obj, type):
            if not _obj_type:
                _obj_type = "class"
            wrapped = obj.__init__  # type: ignore[misc]
            _name = _name or obj.__qualname__
            old_doc = obj.__doc__

            def finalize(_: Callable[..., Any], new_doc: str, /) -> T:
                """Finalize the deprecation of a class."""
                # Can't set new_doc on some extension objects.
                with contextlib.suppress(AttributeError):
                    obj.__doc__ = new_doc

                def warn_if_direct_instance(
                    self: Any, *args: Any, **kwargs: Any
                ) -> Any:
                    """Warn that the class is in beta."""
                    nonlocal warned
                    if not warned and type(self) is obj and not is_caller_internal():
                        warned = True
                        emit_warning()
                    return wrapped(self, *args, **kwargs)

                obj.__init__ = functools.wraps(obj.__init__)(  # type: ignore[misc]
                    warn_if_direct_instance
                )
                # Set __deprecated__ for PEP 702 (IDE/type checker support)
                obj.__deprecated__ = _build_deprecation_message(  # type: ignore[attr-defined]
                    alternative=alternative,
                    alternative_import=alternative_import,
                )
                return obj

        elif isinstance(obj, FieldInfoV1):
            wrapped = None
            if not _obj_type:
                _obj_type = "attribute"
            if not _name:
                msg = f"Field {obj} must have a name to be deprecated."
                raise ValueError(msg)
            old_doc = obj.description

            def finalize(_: Callable[..., Any], new_doc: str, /) -> T:
                return cast(
                    "T",
                    FieldInfoV1(
                        default=obj.default,
                        default_factory=obj.default_factory,
                        description=new_doc,
                        alias=obj.alias,
                        exclude=obj.exclude,
                    ),
                )

        elif isinstance(obj, FieldInfo):
            wrapped = None
            if not _obj_type:
                _obj_type = "attribute"
            if not _name:
                msg = f"Field {obj} must have a name to be deprecated."
                raise ValueError(msg)
            old_doc = obj.description

            def finalize(_: Callable[..., Any], new_doc: str, /) -> T:
                return cast(
                    "T",
                    FieldInfo(
                        default=obj.default,
                        default_factory=obj.default_factory,
                        description=new_doc,
                        alias=obj.alias,
                        exclude=obj.exclude,
                    ),
                )

        elif isinstance(obj, property):
            if not _obj_type:
                _obj_type = "attribute"
            wrapped = None
            _name = _name or cast("type | Callable", obj.fget).__qualname__
            old_doc = obj.__doc__

            class _DeprecatedProperty(property):
                """A deprecated property."""

                def __init__(
                    self,
                    fget: Callable[[Any], Any] | None = None,
                    fset: Callable[[Any, Any], None] | None = None,
                    fdel: Callable[[Any], None] | None = None,
                    doc: str | None = None,
                ) -> None:
                    super().__init__(fget, fset, fdel, doc)
                    self.__orig_fget = fget
                    self.__orig_fset = fset
                    self.__orig_fdel = fdel

                def __get__(self, instance: Any, owner: type | None = None) -> Any:
                    if instance is not None or owner is not None:
                        emit_warning()
                    if self.fget is None:
                        return None
                    return self.fget(instance)

                def __set__(self, instance: Any, value: Any) -> None:
                    if instance is not None:
                        emit_warning()
                    if self.fset is not None:
                        self.fset(instance, value)

                def __delete__(self, instance: Any) -> None:
                    if instance is not None:
                        emit_warning()
                    if self.fdel is not None:
                        self.fdel(instance)

                def __set_name__(self, owner: type | None, set_name: str) -> None:
                    nonlocal _name
                    if _name == "<lambda>":
                        _name = set_name

            def finalize(_: Callable[..., Any], new_doc: str, /) -> T:
                """Finalize the property."""
                prop = _DeprecatedProperty(
                    fget=obj.fget, fset=obj.fset, fdel=obj.fdel, doc=new_doc
                )
                # Set __deprecated__ for PEP 702 (IDE/type checker support)
                prop.__deprecated__ = _build_deprecation_message(  # type: ignore[attr-defined]
                    alternative=alternative,
                    alternative_import=alternative_import,
                )
                return cast("T", prop)

        else:
            _name = _name or cast("type | Callable", obj).__qualname__
            if not _obj_type:
                # edge case: when a function is within another function
                # within a test, this will call it a "method" not a "function"
                _obj_type = "function" if "." not in _name else "method"
            wrapped = obj
            old_doc = wrapped.__doc__

            def finalize(wrapper: Callable[..., Any], new_doc: str, /) -> T:
                """Wrap the wrapped function using the wrapper and update the docstring.

                Args:
                    wrapper: The wrapper function.
                    new_doc: The new docstring.

                Returns:
                    The wrapped function.
                """
                wrapper = functools.wraps(wrapped)(wrapper)
                wrapper.__doc__ = new_doc
                # Set __deprecated__ for PEP 702 (IDE/type checker support)
                wrapper.__deprecated__ = _build_deprecation_message(  # type: ignore[attr-defined]
                    alternative=alternative,
                    alternative_import=alternative_import,
                )
                return cast("T", wrapper)

        old_doc = inspect.cleandoc(old_doc or "").strip("\n")

        # old_doc can be None
        if not old_doc:
            old_doc = ""

        # Modify the docstring to include a deprecation notice.
        if (
            _alternative
            and _alternative.rsplit(".", maxsplit=1)[-1].lower()
            == _alternative.rsplit(".", maxsplit=1)[-1]
        ) or _alternative:
            _alternative = f"`{_alternative}`"

        if (
            _alternative_import
            and _alternative_import.rsplit(".", maxsplit=1)[-1].lower()
            == _alternative_import.rsplit(".", maxsplit=1)[-1]
        ) or _alternative_import:
            _alternative_import = f"`{_alternative_import}`"

        components = [
            _message,
            f"Use {_alternative} instead." if _alternative else "",
            f"Use {_alternative_import} instead." if _alternative_import else "",
            _addendum,
        ]
        details = " ".join([component.strip() for component in components if component])
        package = _package or (
            _name.split(".")[0].replace("_", "-") if "." in _name else None
        )
        if removal:
            if removal.startswith("1.") and package and package.startswith("langchain"):
                removal_str = f"It will not be removed until {package}=={removal}."
            else:
                removal_str = f"It will be removed in {package}=={removal}."
        else:
            removal_str = ""
        new_doc = f"""\
!!! deprecated "{since} {details} {removal_str}"

{old_doc}\
"""

        if inspect.iscoroutinefunction(obj):
            return finalize(awarning_emitting_wrapper, new_doc)
        return finalize(warning_emitting_wrapper, new_doc)