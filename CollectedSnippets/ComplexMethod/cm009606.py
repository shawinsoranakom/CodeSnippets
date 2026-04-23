def beta(
        obj: T,
        *,
        _obj_type: str = obj_type,
        _name: str = name,
        _message: str = message,
        _addendum: str = addendum,
    ) -> T:
        """Implementation of the decorator returned by `beta`."""

        def emit_warning() -> None:
            """Emit the warning."""
            warn_beta(
                message=_message,
                name=_name,
                obj_type=_obj_type,
                addendum=_addendum,
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

        if isinstance(obj, type):
            if not _obj_type:
                _obj_type = "class"
            wrapped = obj.__init__  # type: ignore[misc]
            _name = _name or obj.__qualname__
            old_doc = obj.__doc__

            def finalize(_: Callable[..., Any], new_doc: str, /) -> T:
                """Finalize the annotation of a class."""
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
                return obj

        elif isinstance(obj, property):
            if not _obj_type:
                _obj_type = "attribute"
            wrapped = None
            _name = _name or obj.fget.__qualname__
            old_doc = obj.__doc__

            def _fget(instance: Any) -> Any:
                if instance is not None:
                    emit_warning()
                return obj.fget(instance)

            def _fset(instance: Any, value: Any) -> None:
                if instance is not None:
                    emit_warning()
                obj.fset(instance, value)

            def _fdel(instance: Any) -> None:
                if instance is not None:
                    emit_warning()
                obj.fdel(instance)

            def finalize(_: Callable[..., Any], new_doc: str, /) -> Any:
                """Finalize the property."""
                return property(fget=_fget, fset=_fset, fdel=_fdel, doc=new_doc)

        else:
            _name = _name or obj.__qualname__
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
                return cast("T", wrapper)

        old_doc = inspect.cleandoc(old_doc or "").strip("\n") or ""
        components = [message, addendum]
        details = " ".join([component.strip() for component in components if component])
        new_doc = f".. beta::\n   {details}\n\n{old_doc}\n"

        if inspect.iscoroutinefunction(obj):
            return finalize(awarning_emitting_wrapper, new_doc)
        return finalize(warning_emitting_wrapper, new_doc)