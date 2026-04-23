def reducer_override(
        self, obj: Any
    ) -> tuple[Callable[..., Any], tuple[Any, ...]] | Any:
        import sympy

        if id(obj) in self.empty_values:
            return type(obj).__new__, (type(obj),)

        if inspect.iscode(obj):
            from torch._dynamo.package import SerializedCode

            return type(self)._unpickle_code, (SerializedCode.from_code_object(obj),)

        if id(obj) in self.missing_values:
            return _Missing, ("missing values",)

        if isinstance(obj, torch.Tensor) and obj.device.type != "meta":
            from torch.utils._python_dispatch import is_traceable_wrapper_subclass

            if id(obj) not in self.guard_tree_values:
                return _Missing, ("tensor guard tree",)

            if is_traceable_wrapper_subclass(obj):
                # inner_data is a list of tuples of:
                #   (inner attr name, unpickle func, tuple of func inputs)
                # This supports traceable wrapper subclass inner tensors.
                inner_data = []
                attrs, ctx = obj.__tensor_flatten__()
                # recursively call for inner tensor components
                for attr in attrs:
                    inner = getattr(obj, attr)
                    if isinstance(inner, torch.Tensor):
                        self.guard_tree_values[id(inner)] = inner
                    inner_data.append((attr, inner))

                return type(self)._unpickle_traceable_wrapper_subclass, (
                    torch.empty_like(obj, device="meta"),
                    obj.device,
                    type(obj),
                    torch._C._dispatch_keys(obj).raw_repr(),
                    ctx,
                    inner_data,
                )

            # For FakeTensors, use pytype if set, otherwise default to
            # torch.Tensor. This is important for cross-compilation where
            # we compile with fake tensors but run with real tensors.
            pytype = type(obj)
            if isinstance(obj, torch._subclasses.FakeTensor):
                pytype = obj.pytype if obj.pytype is not None else torch.Tensor

            return type(self)._unpickle_tensor, (
                torch.empty_like(obj, device="meta", requires_grad=obj.requires_grad),
                obj.device,
                pytype,
                torch._C._dispatch_keys(obj).raw_repr(),
                obj.grad,
            )

        elif isinstance(obj, torch.nn.Module):
            if id(obj) not in self.guard_tree_values:
                return _Missing, ("module guard tree",)

            for attr in obj.__dict__.values():
                if isinstance(attr, (torch.Tensor, torch.nn.Module)):
                    continue
                if id(attr) in self.guard_tree_values:
                    continue
                if callable(attr):
                    continue
                self.missing_values[id(attr)] = attr

            # DDP module is a special case because it tries to restore unneeded
            # data in custom __setstate__. We cannot skip ddp module because it
            # is often a toplevel module.
            if isinstance(obj, torch.nn.parallel.DistributedDataParallel):
                return type(self)._unpickle_ddp_module, (obj.__getstate__(),)

            if type(obj).__qualname__ == type(obj).__name__:
                return NotImplemented
            if obj.__class__.__getstate__ == torch.nn.Module.__getstate__:
                return type(self)._unpickle_module, (obj.__getstate__(),)

        elif inspect.ismodule(obj):
            return type(self)._unpickle_python_module, (obj.__name__,)

        elif isinstance(obj, torch._C.DispatchKeySet):
            return type(self)._unpickle_dispatch_key_set, (obj.raw_repr(),)

        elif isinstance(obj, torch._C._functorch.CInterpreter):
            return type(self)._unpickle_functorch_interpreter, (obj.serialize(),)

        elif (
            inspect.isclass(obj)
            and issubclass(obj, sympy.Function)
            and hasattr(obj, "_torch_handler_name")
        ):
            assert hasattr(obj, "_torch_unpickler")
            return obj._torch_unpickler, (obj._torch_handler_name,)

        elif (
            inspect.isclass(obj)
            and issubclass(obj, tuple)
            and hasattr(obj, "_fields")
            and obj.__qualname__ != obj.__name__
        ):
            return type(self)._unpickle_named_tuple_type, (obj.__name__, obj._fields)

        elif isinstance(obj, torch.SymInt):
            raise RuntimeError(f"Cannot serialize SymInt {obj} (node: {obj.node})")

        elif isinstance(obj, types.MappingProxyType):
            return type(self)._unpickle_mapping_proxy, (obj.copy(),)

        elif type(obj) is _COUNT_ITERATOR_TYPE:
            item, step = normalize_count_iter(obj)
            if item is not NotImplemented and step is not NotImplemented:
                return type(self)._unpickle_count_iter, (item, step)

        elif isinstance(obj, torch._dynamo.utils.dict_keys):
            return type(self)._unpickle_dict_keys, (list(obj),)

        elif isinstance(
            obj, torch._ops.OpOverloadPacket
        ) and obj._qualified_op_name.startswith("_C::"):
            return type(self)._unpickle_c_op, (obj.__name__,)

        elif isinstance(obj, torch._ops.OpOverload):
            return type(self)._unpickle_op, (
                obj.namespace,
                obj._opname,
                obj._overloadname,
            )

        elif (
            obj.__class__.__module__ == "builtins"
            and obj.__class__.__name__ == "PyCapsule"
        ):
            # Skipping PyCapsule since there isn't much to be guarded about them.
            return _Missing, ("capsule",)

        elif isinstance(obj, _get_unsupported_types()):
            return _Missing, ("unsupported",)

        elif inspect.isfunction(obj):
            if "<locals>" in obj.__qualname__:
                return type(self)._unpickle_nested_function, (
                    obj.__code__,
                    obj.__module__,
                    obj.__qualname__,
                    obj.__defaults__,
                    obj.__closure__,
                )
            if obj.__module__ in sys.modules:
                f = sys.modules[obj.__module__]
                for name in obj.__qualname__.split("."):
                    f = getattr(f, name, None)  # type: ignore[assignment]
                if f is not obj:
                    return _Missing, ("fqn mismatch",)
        elif inspect.ismethod(obj):
            func = obj.__func__
            method_self = obj.__self__
            inner_func = getattr(method_self, func.__name__)
            if inspect.ismethod(inner_func):
                inner_func = inner_func.__func__
            if func is not inner_func:
                return type(self)._unpickle_bound_method, (func, method_self)

        elif isinstance(obj, type((lambda x: lambda: x)(0).__closure__[0])):  # type: ignore[index] # noqa: PLC3002
            return type(self)._unpickle_cell, (obj.cell_contents,)

        if hasattr(torch.distributed, "distributed_c10d") and isinstance(
            obj, torch.distributed.distributed_c10d.Work
        ):
            if id(obj) not in self.guard_tree_values:
                return _Missing, ("distributed_c10d.Work",)

        if isinstance(obj, torch.nn.attention.SDPBackend):
            return type(self)._unpickle_sdp_backend, (obj.name,)

        if type(obj).__qualname__ != type(obj).__name__ and not isinstance(obj, tuple):
            raise torch._dynamo.exc.PackageError(
                f"Type {type(obj)} for object {obj} cannot be saved "
                + "into torch.compile() package since it's defined in local scope. "
                + "Please define the class at global scope (top level of a module)."
            )

        if (
            inspect.isclass(obj)
            and hasattr(torch.distributed, "fsdp")
            and issubclass(obj, torch.distributed.fsdp._fully_shard.FSDPModule)
        ):
            if obj is not torch.distributed.fsdp._fully_shard.FSDPModule:
                original_type = obj.__mro__[2]
                assert issubclass(original_type, torch.nn.Module)
                assert (
                    original_type
                    in torch.distributed.fsdp._fully_shard._fully_shard.get_cls_to_fsdp_cls()
                )
                return type(self)._unpickle_fsdp_module_type, (original_type,)

        return NotImplemented