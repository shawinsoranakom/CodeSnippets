def reducer_override(
        self, obj: object
    ) -> tuple[Callable[..., Any], tuple[Any, ...]]:
        # This function is supposed to return either NotImplemented (meaning to
        # do the default pickle behavior) or a pair of (unpickle callable, data
        # to pass to unpickle).

        # We could instead teach individual classes how to pickle themselves but
        # that has a few problems:
        #
        #   1. If we have some special needs (maybe for this use-case we don't
        #      want to fully serialize every field) then we're adding private
        #      details to a public interface.
        #
        #   2. If we need to have some common shared data (such as a
        #      FakeTensorMode) which is passed to each value it's harder to
        #      support.

        # These are the types that need special handling. See the individual
        # *PickleData classes for details on pickling that particular type.
        if isinstance(obj, FakeTensor):
            return _TensorPickleData.reduce_helper(self, obj)
        elif isinstance(obj, torch.fx.GraphModule):
            return _GraphModulePickleData.reduce_helper(self, obj)
        elif isinstance(obj, (torch._ops.OperatorBase, torch._ops.OpOverloadPacket)):
            return _OpPickleData.reduce_helper(self, obj)
        elif isinstance(obj, ShapeEnv):
            return _ShapeEnvPickleData.reduce_helper(self, obj)
        elif isinstance(obj, torch.SymInt):
            return _SymNodePickleData.reduce_helper(self, obj)
        elif isinstance(obj, torch._guards.TracingContext):
            return _TracingContextPickleData.reduce_helper(self, obj)
        elif isinstance(obj, FakeScriptObject):
            # FakeScriptObjects wrap opaque traced objects (e.g. DeviceMesh,
            # ProcessGroup) that can't be default-pickled. Reduce to None
            # since they aren't meaningful after deserialization.
            return (_unpickle_as_none, ())
        elif isinstance(obj, weakref.ref):
            # Serialize weakrefs properly: if the referent is alive,
            # serialize it and reconstruct the weakref on unpickle.
            # If the referent is dead, unpickle as a dead-weakref-like callable.
            referent = obj()
            if referent is not None:
                return (_unpickle_as_weakref, (referent,))
            else:
                return (_unpickle_as_dead_weakref, ())
        else:
            # We should never get a raw Node!
            if isinstance(obj, torch.fx.Node):
                if self.options.ignore_raw_node:
                    return (_unpickle_as_none, ())
                raise AssertionError("Unexpected raw Node during pickling")
            if reduce := _TorchNumpyPickleData.reduce_helper(self, obj):
                return reduce

            # returning `NotImplemented` causes pickle to revert to the default
            # behavior for this object.
            return NotImplemented