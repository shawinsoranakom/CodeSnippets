def create_arg(self, a: Any) -> Argument:
        """
        A method that lowers the objects seen as arguments during symbolic evaluation
        into Argument types that can be stored in IR.

        Can be override to support more trace-specific types.
        """
        # IMPORTANT: Are you here because you are trying to proxy a new type into
        # the graph? Please Please Please contact someone on the PyTorch Compiler team;
        # the considerations are subtle.
        #
        # 1) When you add a new type, all of the downstream consumers and pass writers
        # need to handle the new type. torch.fx is intended to be easy to write
        # passes for, so we will push back against new types.
        # 2) In torch.compile's IR, there are only specific operations that go
        # into the graph. In particular, Tensor operations should go into the graph,
        # but non-Tensor operations shouldn't. What that means is that constructors
        # for new types *SHOULD NOT* become nodes in the FX graph.
        handler = _create_arg_bypass.get(type(a))
        if handler is not None:
            # this is just a performance optimization and can be removed if needed
            # for common types, we have a fast path to avoid isinstance() overhead
            # this doesn't remove the checks below since we need to handle subclasses
            return handler(self, a)

        if isinstance(a, Proxy):
            return a.node  # most common arg type goes first
        elif hasattr(a, "__fx_create_arg__"):
            return a.__fx_create_arg__(self)
        # aggregates
        elif isinstance(a, tuple):
            if hasattr(a, "_fields"):
                # NamedTuple constructors don't seem to like getting a generator
                # expression as an argument to their constructor, so build this
                # intermediate tuple and unpack it into the NamedTuple constructor
                args = [self.create_arg(elem) for elem in a]
                return type(a)(*args)  # type: ignore[arg-type]
            return type(a)([self.create_arg(elem) for elem in a])
        elif isinstance(a, list):
            return [self.create_arg(elem) for elem in a]
        elif isinstance(a, dict):
            return _create_arg_dict(self, a)
        elif isinstance(a, slice):
            return slice(
                self.create_arg(a.start),
                self.create_arg(a.stop),
                self.create_arg(a.step),
            )

        elif isinstance(a, range):
            return range(  # pyrefly: ignore[no-matching-overload]
                self.create_arg(a.start),  # pyrefly: ignore[bad-argument-type]
                self.create_arg(a.stop),  # pyrefly: ignore[bad-argument-type]
                self.create_arg(a.step),  # pyrefly: ignore[bad-argument-type]
            )

        elif isinstance(a, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)):
            return a  # pyrefly: ignore[bad-return]

        elif is_opaque_value_type(type(a)):
            return a

        elif is_dataclass(a):
            kwargs = {
                field.name: self.create_arg(getattr(a, field.name))
                for field in fields(a)
            }
            return self.create_node("call_function", a.__class__, (), kwargs)

        elif isinstance(a, (*base_types, enum.Enum)) or a is None or a is ...:
            return a  # pyrefly: ignore[bad-return]

        raise NotImplementedError(f"argument of type: {type(a)}")