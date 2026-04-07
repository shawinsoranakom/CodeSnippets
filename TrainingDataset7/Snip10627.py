def _validate_force_insert(cls, force_insert):
        if force_insert is False:
            return ()
        if force_insert is True:
            return (cls,)
        if not isinstance(force_insert, tuple):
            raise TypeError("force_insert must be a bool or tuple.")
        for member in force_insert:
            if not isinstance(member, ModelBase):
                raise TypeError(
                    f"Invalid force_insert member. {member!r} must be a model subclass."
                )
            if not issubclass(cls, member):
                raise TypeError(
                    f"Invalid force_insert member. {member.__qualname__} must be a "
                    f"base of {cls.__qualname__}."
                )
        return force_insert