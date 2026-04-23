def _getattr_static(self, name: str) -> object:
        if name in self._looked_up_attrs:
            return self._looked_up_attrs[name]

        subobj = inspect.getattr_static(self.value, name, NO_SUCH_SUBOBJ)

        # In some cases, we have to do dynamic lookup because getattr_static is not enough. For example, threading.local
        # has side-effect free __getattribute__ and the attribute is not visible without a dynamic lookup.
        # NOTE we assume the following descriptors are side-effect-free as far
        # as Dynamo tracing is concerned.
        #
        # C-level descriptors (getset_descriptor for __dict__, member_descriptor
        # for __slots__) are always safe to resolve — their __get__ is
        # implemented in C and doesn't run user code, so __getattribute__
        # overrides are irrelevant.  The NO_SUCH_SUBOBJ and
        # _is_c_defined_property cases DO require the absence of a custom
        # __getattribute__ because they fall back to
        # type(self.value).__getattribute__ which could be user-overridden.
        if inspect.ismemberdescriptor(subobj) or inspect.isgetsetdescriptor(subobj):
            subobj = type(self.value).__getattribute__(self.value, name)
        elif not self._object_has_getattribute and (
            subobj is NO_SUCH_SUBOBJ  # e.g., threading.local
            or self._is_c_defined_property(subobj)
        ):
            # Call __getattribute__, we have already checked that this is not overridden and side-effect free. We don't
            # want to call getattr because it can be user-overridden.
            subobj = type(self.value).__getattribute__(self.value, name)
        elif self._object_has_getattribute and subobj is NO_SUCH_SUBOBJ:
            # If the object has an overridden getattribute method, Dynamo has
            # already tried tracing it, and encountered an AttributeError. We
            # call getattr_static only when the __getattribute__ tracing fails
            # (check var_getattr impl). So, it is safe here to raise the
            # AttributeError.
            raise AttributeError

        self._looked_up_attrs[name] = subobj
        return subobj