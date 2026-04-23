def serialize_input(self, arg, arg_type: Any | None = None) -> Argument:
        import torch._inductor.ir as inductor_ir

        inductor_tensor_buffers = (
            inductor_ir.Buffer,
            inductor_ir.ReinterpretView,
        )

        if isinstance(arg, torch.fx.Node):
            if arg.op == "get_attr":
                if not isinstance(arg.target, str):
                    raise AssertionError(
                        f"expected arg.target to be str, got {type(arg.target).__name__}"
                    )
                attr = getattr(arg.graph.owning_module, arg.target)

                if isinstance(attr, torch.Tensor):
                    raise SerializeError(
                        "getattr nodes containing tensors should not appear in the graph"
                    )
                elif isinstance(attr, torch.fx.GraphModule):
                    with self.save_graph_state():
                        graph = self.serialize_graph(attr)
                    return Argument.create(
                        as_graph=GraphArgument(name=arg.target, graph=graph)
                    )
                elif type(attr).__name__ == "LoweredBackendModule":
                    # Special handling for executorch_call_delegate HOP
                    # It's first argument is a LoweredBackendModule, for which we
                    # serialize name and backend id of the lowered module
                    module_name = getattr(attr, "module_name", None)
                    backend_id = getattr(attr, "backend_id", None)
                    if module_name is None:
                        raise AssertionError("module_name should not be None")
                    if backend_id is None:
                        raise AssertionError("backend_id should not be None")
                    return Argument.create(as_string=f"{module_name}-{backend_id}")
                else:
                    raise SerializeError(
                        f"Unsupported getattr attribute {arg.target} with type: {type(attr)}"
                    )
            elif self.is_sym_int_arg(arg):
                return Argument.create(
                    as_sym_int=SymIntArgument.create(as_name=arg.name)
                )
            elif self.is_sym_float_arg(arg):
                return Argument.create(
                    as_sym_float=SymFloatArgument.create(as_name=arg.name)
                )
            elif self.is_sym_bool_arg(arg):
                return Argument.create(
                    as_sym_bool=SymBoolArgument.create(as_name=arg.name)
                )
            elif isinstance(arg.meta["val"], ep.CustomObjArgument):
                return Argument.create(
                    as_custom_obj=CustomObjArgument(
                        name=arg.name, class_fqn=arg.meta["val"].class_fqn
                    )
                )
            elif arg.name in self.duplicate_getitem_nodes:
                dedup_name = self.duplicate_getitem_nodes[arg.name]
                return Argument.create(as_tensor=TensorArgument(name=dedup_name))
            else:
                return Argument.create(as_tensor=TensorArgument(name=arg.name))
        elif isinstance(arg, inductor_tensor_buffers):
            # Other branches are for arguments in fx node.
            # This is a special branch for handling buffers (representing tensor arguments)
            # for inductor's ExternalFallbackNode
            # export_extern_kernel_node() is using this function to serialize arguments
            arg_name = arg.get_name()
            if arg_name is None:
                raise AssertionError("Buffer must have valid name")
            return Argument.create(as_tensor=TensorArgument(name=arg_name))
        elif isinstance(arg, inductor_ir.TorchBindObject):
            # This is a special branch for handling TorchBindObject
            # for inductor's ExternalFallbackNode
            # export_extern_kernel_node() is using this function to serialize arguments
            arg_name = arg.get_name()
            if arg_name is None:
                raise AssertionError("Buffer must have valid name")
            arg_val = arg.get_real_obj()
            class_fqn = arg_val._type().qualified_name()
            self.custom_objs[arg_name] = arg_val
            return Argument.create(as_custom_obj=CustomObjArgument(arg_name, class_fqn))
        elif isinstance(arg, torch.SymInt):
            # This is a special branch for handling SymInt args in inductor's
            # ExternalFallbackNode.
            # For regular FX graph, SymInt arg should be a fx.Node with
            # self.is_sym_int_arg(arg) being true
            return Argument.create(as_sym_int=SymIntArgument.create(as_name=str(arg)))
        elif isinstance(arg, torch.SymFloat):
            # This is a special branch for handling SymFloat args in inductor's
            # ExternalFallbackNode.
            # For regular FX graph, SymInt arg should be a fx.Node with
            # self.is_sym_float_arg(arg) being true
            return Argument.create(
                as_sym_float=SymFloatArgument.create(as_name=str(arg))
            )
        elif type(arg) is bool:
            return Argument.create(as_bool=arg)
        elif type(arg) is str:
            return Argument.create(as_string=arg)
        elif type(arg) is int:
            return Argument.create(as_int=arg)
        elif type(arg) is float:
            return Argument.create(as_float=arg)
        elif type(arg) is complex:
            return Argument.create(
                as_complex=ComplexValue(real=arg.real, imag=arg.imag)
            )
        elif arg is None:
            return Argument.create(as_none=True)
        elif isinstance(arg, dict):
            serialized_dict = {}
            for key, value in arg.items():
                if not isinstance(key, str):
                    raise SerializeError(f"Dict keys must be strings, got {type(key)}")
                serialized_dict[key] = self.serialize_input(value)
            return Argument.create(as_string_to_argument=serialized_dict)
        elif isinstance(arg, (list, tuple)):
            if len(arg) == 0:
                if arg_type is not None:
                    if isinstance(arg_type, torch.OptionalType):
                        arg_type = arg_type.getElementType()  # type: ignore[assignment]
                    if not isinstance(arg_type, torch.ListType):
                        raise AssertionError(
                            f"expected ListType, got {type(arg_type).__name__}"
                        )
                    elem_type = arg_type.getElementType()
                    if isinstance(elem_type, torch.OptionalType):
                        elem_type = elem_type.getElementType()

                    if isinstance(elem_type, torch.BoolType):
                        return Argument.create(as_bools=[])
                    elif isinstance(elem_type, torch.IntType):
                        return Argument.create(as_ints=[])
                    elif isinstance(elem_type, torch.FloatType):
                        return Argument.create(as_floats=[])
                    elif isinstance(elem_type, torch.StringType):
                        return Argument.create(as_strings=[])
                    elif isinstance(elem_type, torch.TensorType):
                        return Argument.create(as_tensors=[])
                    else:
                        # I believe empty symint lists default to ints, but
                        # please file an issue if this is not the case
                        raise SerializeError(f"Empty list with type {elem_type} nyi.")
                else:
                    # We could serialize this by default to a tensor list. This
                    # is needed in the HOO case
                    log.warning(
                        "Unsure how to serialize the given empty list, "
                        "as we don't know what is the type of this argument. "
                        "Serializing it as a tensor list by default."
                    )
                    return Argument.create(as_tensors=[])

            if all(type(a) is bool for a in arg):
                return Argument.create(as_bools=list(arg))
            elif all(type(a) is int for a in arg):
                return Argument.create(as_ints=list(arg))
            elif all(type(a) is float for a in arg):
                return Argument.create(as_floats=list(arg))
            elif all(type(a) is str for a in arg):
                return Argument.create(as_strings=list(arg))
            elif all(self.is_inductor_sym_int_arg(a) for a in arg):
                # This is a special branch for handling SymInt args in inductor's
                # ExternalFallbackNode.
                # For regular FX graph, SymInt arg should be a fx.Node
                values = []
                for a in arg:
                    if isinstance(a, torch.SymInt):
                        values.append(SymIntArgument.create(as_name=str(a)))
                    elif type(a) is int:
                        values.append(SymIntArgument.create(as_int=a))
                return Argument.create(as_sym_ints=values)
            elif all(isinstance(a, torch.SymFloat) for a in arg):
                return Argument.create(
                    as_sym_floats=[SymFloatArgument.create(as_name=str(a)) for a in arg]
                )
            elif all(self.is_sym_int_arg(a) for a in arg):
                # list of sym_ints
                values = []
                for a in arg:
                    if isinstance(a, torch.fx.Node):
                        values.append(SymIntArgument.create(as_name=a.name))
                    elif type(a) is int:
                        values.append(SymIntArgument.create(as_int=a))
                return Argument.create(as_sym_ints=values)
            elif all(self.is_sym_float_arg(a) for a in arg):
                # list of sym_float
                values = []
                for a in arg:
                    if isinstance(a, torch.fx.Node):
                        values.append(SymFloatArgument.create(as_name=a.name))
                    elif isinstance(a, float):
                        values.append(SymFloatArgument.create(as_float=a))
                return Argument.create(as_sym_floats=values)
            elif all(self.is_sym_bool_arg(a) for a in arg):
                # list of sym_bools
                values = []
                for a in arg:
                    if isinstance(a, torch.fx.Node):
                        values.append(SymBoolArgument.create(as_name=a.name))
                    elif isinstance(a, bool):
                        values.append(SymBoolArgument.create(as_bool=a))
                return Argument.create(as_sym_bools=values)
            elif all(isinstance(a, torch.fx.Node) for a in arg):
                # list of tensors
                arguments = []
                for a in arg:
                    if a.op == "get_attr":
                        raise SerializeError(
                            "getattr nodes containing tensors should not appear in the graph"
                        )
                    arguments.append(TensorArgument(name=a.name))
                return Argument.create(as_tensors=arguments)
            elif all(isinstance(a, (list, tuple)) for a in arg) and all(
                all(isinstance(t, torch.fx.Node) for t in inner) for inner in arg
            ):
                # nested list of tensors (List[List[Tensor]])
                nested_arguments = []
                for inner_list in arg:
                    inner_arguments = []
                    for node in inner_list:
                        if node.op == "get_attr":
                            raise SerializeError(
                                "getattr nodes containing tensors should not appear in the graph"
                            )
                        inner_arguments.append(TensorArgument(name=node.name))
                    nested_arguments.append(inner_arguments)
                return Argument.create(as_nested_tensors=nested_arguments)
            elif all(isinstance(a, (torch.fx.Node, type(None))) for a in arg):
                # list of optional tensors
                def serialize_optional_tensor_args(a):
                    if a is None:
                        return OptionalTensorArgument.create(as_none=True)
                    elif isinstance(a, torch.fx.Node):
                        return OptionalTensorArgument.create(
                            as_tensor=TensorArgument(name=a.name)
                        )
                    else:
                        raise SerializeError(f"Unsupported list/tuple argument: {a}")

                return Argument.create(
                    as_optional_tensors=list(map(serialize_optional_tensor_args, arg))
                )
            elif all(isinstance(a, inductor_tensor_buffers) for a in arg):
                # list of inductor buffers
                return Argument.create(
                    as_tensors=[TensorArgument(name=a.get_name()) for a in arg],
                )
            elif all(
                isinstance(a, (*inductor_tensor_buffers, type(None))) for a in arg
            ):
                # list of inductor buffers as optional tensors
                def serialize_optional_tensor_args(a):
                    if a is None:
                        return OptionalTensorArgument.create(as_none=True)
                    elif isinstance(a, inductor_tensor_buffers):
                        return OptionalTensorArgument.create(
                            as_tensor=TensorArgument(name=a.get_name())
                        )
                    else:
                        raise SerializeError(f"Unsupported list/tuple argument: {a}")

                return Argument.create(
                    as_optional_tensors=list(map(serialize_optional_tensor_args, arg))
                )
            elif all(
                isinstance(a, tuple) and all(type(x) is int for x in a) for a in arg
            ):
                # list of int tuples
                return Argument.create(as_int_lists=[list(t) for t in arg])
            elif all(
                isinstance(a, (list, tuple)) and all(isinstance(x, float) for x in a)
                for a in arg
            ):
                # list of float lists (List[List[float]])
                return Argument.create(as_float_lists=[list(t) for t in arg])
            else:
                raise SerializeError(
                    f"Unsupported list/tuple argument type: {[type(a) for a in arg]}"
                )
        elif isinstance(arg, torch.dtype):
            return Argument.create(as_scalar_type=_TORCH_TO_SERIALIZE_DTYPE[arg])
        elif isinstance(arg, torch.device):
            return Argument.create(as_device=Device(type=arg.type, index=arg.index))
        elif isinstance(arg, torch.memory_format):
            return Argument.create(
                as_memory_format=_TORCH_TO_SERIALIZE_MEMORY_FORMAT[arg]
            )
        elif isinstance(arg, torch.layout):
            return Argument.create(as_layout=_TORCH_TO_SERIALIZE_LAYOUT[arg])
        elif isinstance(arg, torch._C.ScriptObject):
            if not (
                arg._has_method("__getstate__")  # type: ignore[attr-defined]
                and arg._has_method("__setstate__")  # type: ignore[attr-defined]
            ):
                raise SerializeError(
                    f"Unable to serialize custom class {arg}. Please define "
                    "serialization methods via def_pickle()."
                )
            # Custom objects through torchind are serializable with pickle,
            # through implementing the .def_pickle function.  This should result
            # in the object containing a __getstate__ and __setstate__
            # serialize/deserialize function.
            custom_obj_name = f"_custom_obj_{len(self.custom_objs)}"
            self.custom_objs[custom_obj_name] = arg
            class_fqn = arg._type().qualified_name()  # type: ignore[attr-defined]
            return Argument.create(
                as_custom_obj=CustomObjArgument(custom_obj_name, class_fqn)
            )
        elif isinstance(arg, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)):
            return Argument.create(as_operator=self.serialize_operator(arg))
        else:
            raise SerializeError(
                f"Unsupported argument type: {type(arg)} with schema arg_type {arg_type}"
            )