def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.lockfile is None:
            raise ValueError(
                "{}.lockfile isn't set. Set it to a unique value "
                "in the base class.".format(cls.__name__)
            )