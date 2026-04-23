def emit_node(node: Node) -> None:
            maybe_type_annotation = (
                "" if node.type is None else f" : {type_repr(node.type)}"
            )
            maybe_comment = ""

            if verbose:
                # override annotation with more detailed information
                try:
                    from torch.distributed.tensor._api import DTensor, DTensorSpec

                    dtensorspec_format_shard_order_str = (
                        DTensorSpec.format_shard_order_str
                    )
                except ModuleNotFoundError:
                    DTensor = None  # type: ignore[assignment,misc]
                    dtensorspec_format_shard_order_str = None
                from torch.fx.experimental.proxy_tensor import py_sym_types
                from torch.fx.passes.shape_prop import TensorMetadata

                meta_val = node.meta.get(
                    "val",
                    node.meta.get("tensor_meta", node.meta.get("example_value", None)),
                )

                def _tensor_annotation(t: torch.Tensor) -> str:
                    stride = stringify_shape(t.stride()) if include_stride else ""
                    device = f"{t.device}" if include_device else ""
                    return (
                        f"{red(dtype_abbrs[t.dtype])}"
                        f"{blue(stringify_shape(t.shape))}"
                        f"{dim_blue(stride)}"
                        f"{dim_green(device)}"
                    )

                # use string as annotation, to make it valid python code
                if isinstance(meta_val, torch.Tensor) and meta_val.layout not in (
                    torch.sparse_csc,
                    torch.sparse_csr,
                ):
                    # Fake tensors cause tests to wobble, so do not custom print them.
                    is_plain = type(meta_val) is torch.Tensor or isinstance(
                        meta_val, torch._subclasses.FakeTensor
                    )
                    core = _tensor_annotation(meta_val)
                    if is_plain:
                        maybe_type_annotation = f': "{core}"'
                    elif type(meta_val) is DTensor:
                        if dtensorspec_format_shard_order_str is None:
                            raise AssertionError(
                                "dtensorspec_format_shard_order_str is None for DTensor"
                            )
                        dtensor_meta = dtensorspec_format_shard_order_str(
                            meta_val._spec.placements,  # type: ignore[attr-defined]
                            meta_val._spec.shard_order,  # type: ignore[attr-defined]
                        )
                        cls = meta_val.__class__.__name__
                        maybe_type_annotation = (
                            f': "{cls}({core}, {dim_green(dtensor_meta)})"'
                        )
                    else:
                        cls = meta_val.__class__.__name__
                        maybe_type_annotation = f': "{cls}({core})"'

                elif isinstance(meta_val, py_sym_types):
                    val_str = CodeGen._sym_repr(meta_val)
                    maybe_type_annotation = f': "Sym({val_str})"'

                elif isinstance(meta_val, TensorMetadata):
                    maybe_type_annotation = f': "{dtype_abbrs[meta_val.dtype]}{stringify_shape(meta_val.shape)}"'

            desc = None
            if expanded_def:
                desc = node.meta.get("desc", None)
                if desc is not None and node.op == "placeholder":
                    maybe_comment += f"  # {desc}"
                # output is handled specially

            if include_meta and hasattr(node, "meta") and node.meta:
                body.append('"""\n')
                for k, v in node.meta.items():
                    # use str over repr since repr is susceptible to sympy
                    # errors such as "cannot determine truth value of Relational"
                    # Pretty print the high-level dict with str() for values
                    body.append(
                        f"{k}: {pprint.pformat(str(v), width=80, compact=True)}\n"
                    )
                body.append('"""\n')

            if node.op == "placeholder":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str, got {type(node.target)}"
                    )
                maybe_default_arg = (
                    "" if not node.args else f" = {_get_repr(node.args[0])}"
                )
                free_vars.append(
                    f"{node.target}{maybe_type_annotation}{maybe_default_arg}{maybe_comment}"
                )
                raw_name = node.target.replace("*", "")
                if raw_name != repr(node):
                    body.append(f"{repr(node)} = {raw_name}\n")
                return
            elif node.op == "call_method":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for call_method, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {_format_target(_get_repr(node.args[0]), node.target)}"
                    f"({_format_args(node.args[1:], node.kwargs)})"
                )
                return
            elif node.op == "call_function":
                if not callable(node.target):
                    raise AssertionError(
                        f"Expected node.target to be callable, got {type(node.target)}"
                    )
                # pretty print operators
                if (
                    getattr(node.target, "__module__", "") == "_operator"
                    and node.target.__name__ in magic_methods
                ):
                    if not isinstance(node.args, tuple):
                        raise AssertionError(
                            f"Expected node.args to be tuple, got {type(node.args)}"
                        )
                    body.append(
                        f"{repr(node)}{maybe_type_annotation} = "
                        f"{magic_methods[node.target.__name__].format(*(_get_repr(a) for a in node.args))}"
                    )
                    return

                # pretty print inplace operators; required for jit.script to work properly
                # not currently supported in normal FX graphs, but generated by torchdynamo
                if (
                    getattr(node.target, "__module__", "") == "_operator"
                    and node.target.__name__ in inplace_methods
                ):
                    body.append(
                        f"{inplace_methods[node.target.__name__].format(*(_get_repr(a) for a in node.args))};  "
                        f"{repr(node)}{maybe_type_annotation} = {_get_repr(node.args[0])}"
                    )
                    return

                qualified_name = _get_qualified_name(node.target)
                global_name = add_global(qualified_name, node.target)
                # special case for getattr: node.args could be 2-argument or 3-argument
                # 2-argument: attribute access; 3-argument: fall through to attrib function call with default value
                if (
                    global_name == "getattr"
                    and isinstance(node.args, tuple)
                    and isinstance(node.args[1], str)
                    and node.args[1].isidentifier()
                    and len(node.args) == 2
                ):
                    body.append(
                        f"{repr(node)}{maybe_type_annotation} = {_format_target(_get_repr(node.args[0]), node.args[1])}"
                    )
                    return
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {global_name}({_format_args(node.args, node.kwargs)})"
                )
                if node.meta.get("is_wrapped", False):
                    wrapped_fns.setdefault(global_name)
                return
            elif node.op == "call_module":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for call_module, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = "
                    f"{_format_target(root_module, node.target)}({_format_args(node.args, node.kwargs)})"
                )
                return
            elif node.op == "get_attr":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for get_attr, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {_format_target(root_module, node.target)}"
                )
                return
            elif node.op == "output":
                if node.type is not None:
                    maybe_return_annotation[0] = f" -> {type_repr(node.type)}"
                body.append(
                    self._call_method_with_signature_check(
                        self.generate_output,
                        node.args[0],
                        descs=desc if expanded_def else None,
                        repr_fn=_get_repr,
                    )
                )
                return
            raise NotImplementedError(f"node: {node.op} {node.target}")