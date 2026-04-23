def inner_func(*args, **kwargs) -> Any:
        if len(args) == 2:
            warnings.warn(
                f"The argument order of {func.__name__} has been changed. "
                "Please check the document to avoid future breakages.",
                stacklevel=2,
            )
            sig = inspect.signature(func)
            kwonlyargs = [
                p.name for p in sig.parameters.values() if p.kind == p.KEYWORD_ONLY
            ]
            if "storage_writer" in kwonlyargs:
                if "storage_writer" in kwargs:
                    raise AssertionError(f"storage_writer in kwargs: {(args, kwargs)}")
                kwargs["storage_writer"] = args[1]
            elif "storage_reader" in kwonlyargs:
                if "storage_reader" in kwargs:
                    raise AssertionError(f"storage_reader in kwargs: {(args, kwargs)}")
                kwargs["storage_reader"] = args[1]
            else:
                raise RuntimeError(f"Unexpected kwonlyargs = {kwonlyargs}")
            return func(args[0], **kwargs)
        else:
            return func(*args, **kwargs)