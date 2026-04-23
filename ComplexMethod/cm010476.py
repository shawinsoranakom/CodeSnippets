def _prep_args_for_hash(
        self,
        result: list[object],
        args: Mapping[str, object] | Sequence[object] | Iterable[object],
        state: _CacheKeyState,
        id_hashed_objects: list[object],
    ) -> None:
        """
        Translate the provided args into a form suitable for caching at FakeTensor
        dispatch, i.e., convert unhashable types like lists & dicts into tuples and
        convert FakeTensors into metadata. Raises _BypassDispatchCache to signal
        unsupported cases that should bypass caching.
        """
        from torch._higher_order_ops.auto_functionalize import (
            FunctionalCallableWithEpilogue,
        )
        from torch._higher_order_ops.utils import FunctionalizeCtxWrapper

        if isinstance(args, (list, tuple, dict)):
            result.append(type(args))
            result.append(f"length_{len(args)}")

        if isinstance(args, dict):
            self._prep_args_for_hash(result, args.keys(), state, id_hashed_objects)
            self._prep_args_for_hash(result, args.values(), state, id_hashed_objects)
            return

        for arg in args:
            if isinstance(arg, FakeTensor):
                if not self.is_our_fake(arg):
                    raise _BypassDispatchCache("not our fake")
                if arg.constant is not None:
                    raise _BypassDispatchCache("constant attribute")
                if is_sparse_any(arg):
                    raise _BypassDispatchCache(f"{arg.layout} tensor")
                metadata = extract_tensor_metadata(arg)
                metadata._flatten_into(result, self, state)
            elif isinstance(arg, Tensor):
                raise _BypassDispatchCache("non-fake tensor")
            elif isinstance(arg, SymInt):
                state.convert_sym_int(result, arg)
            elif isinstance(arg, (SymBool, SymFloat)):
                raise _BypassDispatchCache("symbolic shape")
            elif isinstance(arg, (list, tuple, dict)):
                self._prep_args_for_hash(result, arg, state, id_hashed_objects)
            elif isinstance(arg, types.FunctionType):
                raise _BypassDispatchCache("function argument")
            elif isinstance(arg, torch.fx.GraphModule):
                # This is used for invoke_subgraph where id(graph_module) allows
                # us to cache fake outputs
                result.append(type(arg))
                result.append(id(arg))
                id_hashed_objects.append(arg)
            elif isinstance(arg, FunctionalizeCtxWrapper):
                # Special case for AOT Dispatcher first pass, where the fake
                # tensor is called on the functional wrapper of the subgraph.
                result.append(hash(arg))
                # functional wrapper is destroyed after fake tensor prop. We
                # need to put the finalizer on the subgraph.
                id_hashed_objects.append(arg.subgraph)
            elif isinstance(arg, FunctionalCallableWithEpilogue):
                result.append(type(arg))
                result.append(hash(arg))
                id_hashed_objects.append(arg.orig_callable)
            else:
                # It's important to capture the type of the arg since, e.g., 1 and 1.0
                # hash to the same value, but can produce different dtypes for the
                # output tensor.
                result.append(type(arg))
                result.append(arg)