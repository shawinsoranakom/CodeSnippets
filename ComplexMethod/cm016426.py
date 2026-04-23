def decorator(cls: T) -> T:
        if isinstance(cls, _ComfyType) or issubclass(cls, _ComfyType):
            # clone Input and Output classes to avoid modifying the original class
            new_cls = cls
            if hasattr(new_cls, "Input"):
                new_cls.Input = copy_class(new_cls.Input)
            if hasattr(new_cls, "Output"):
                new_cls.Output = copy_class(new_cls.Output)
        else:
            # copy class attributes except for special ones that shouldn't be in type()
            cls_dict = {
                k: v for k, v in cls.__dict__.items()
                if k not in ('__dict__', '__weakref__', '__module__', '__doc__')
            }
            # new class
            new_cls: ComfyTypeIO = type(
                cls.__name__,
                (cls, ComfyTypeIO),
                cls_dict
            )
            # metadata preservation
            new_cls.__module__ = cls.__module__
            new_cls.__doc__ = cls.__doc__
            # assign ComfyType attributes, if needed
        new_cls.io_type = io_type
        if hasattr(new_cls, "Input") and new_cls.Input is not None:
            new_cls.Input.Parent = new_cls
        if hasattr(new_cls, "Output") and new_cls.Output is not None:
            new_cls.Output.Parent = new_cls
        return new_cls