def _check_graph_module(self, gm: torch.fx.GraphModule) -> None:
        def _allowed_getattr_types(is_toplevel_gm) -> tuple[type[Any], ...]:
            if is_toplevel_gm:
                ret = self.allowed_getattr_types()
            else:
                ret = self.allowed_getattr_types_for_subgm()
            if any(t is object for t in ret):
                raise AssertionError("allowed_getattr_types must not contain 'object'")
            return ret

        def _check_valid_op(op) -> None:
            def _allowed_builtin_ops() -> list:
                ret = self.allowed_builtin_ops()
                if not all(inspect.isbuiltin(op) for op in ret):
                    raise AssertionError("allowed_builtin_ops must all be builtins")
                return ret

            def _allowed_op_types() -> tuple[type[Any], ...]:
                ret = self.allowed_op_types()
                if any(t is object for t in ret):
                    raise AssertionError("allowed_op_types must not contain 'object'")
                return ret

            # TODO Remove this allowlist.
            _allowed_torch_functions = (
                torch.autograd.grad_mode.set_grad_enabled,
                torch.sym_int,
                torch.sym_float,
                torch.sym_ite,
                torch.sym_max,
                torch.sym_min,
                torch.sym_not,
                torch.sym_sqrt,
                torch.sym_sum,
                torch.export.custom_ops._call_custom_autograd_function_in_pre_dispatch,
                # TODO (tmanlaibaatar)
                # Predispatch export is able to contain autograd ops.
                # These will be modeled as HOO later
                torch._C._set_grad_enabled,
                torch.amp.autocast_mode._enter_autocast,
                torch.amp.autocast_mode._exit_autocast,
                torch.fx.experimental.symbolic_shapes.cast_symbool_to_symint_guardless,
                torch._functorch.predispatch._add_batch_dim,
                torch._functorch.predispatch._remove_batch_dim,
                torch._functorch.predispatch._vmap_increment_nesting,
                torch._functorch.predispatch._vmap_decrement_nesting,
                torch._functorch.predispatch.lazy_load_decompositions,
                torch._functorch.predispatch._make_dual,
                torch._functorch.predispatch._unpack_dual,
                torch._functorch.predispatch._jvp_increment_nesting,
                torch._functorch.predispatch._jvp_decrement_nesting,
                torch._functorch.predispatch._unwrap_for_grad,
                torch._functorch.predispatch._enter_dual_level,
                torch._functorch.predispatch._exit_dual_level,
            )

            if not isinstance(op, _allowed_op_types()):
                if (
                    op not in _allowed_builtin_ops()
                    and op not in _allowed_torch_functions
                ):
                    raise SpecViolationError(
                        f"Operator '{op}' is not an allowed operator type: {_allowed_op_types()}\n"
                        f"Valid builtin ops: {_allowed_builtin_ops()}"
                        f"Valid torch functions: {_allowed_torch_functions}"
                    )

            if isinstance(op, OpOverload):
                # All ops functional
                # TODO (tmanlaibaatar) more proper way is needed here
                if self.dialect != "TRAINING" and not is_functional(op):
                    raise SpecViolationError(f"operator '{op}' is not functional")
            self.check_valid_op(op)

        for mod in gm.modules():
            is_toplevel_gm = mod is gm

            if not isinstance(mod, torch.fx.GraphModule):
                continue

            mod.graph.lint()
            for node in mod.graph.nodes:
                # TODO(T140410192): should have fake tensor for all dialects
                if node.op in {"call_module", "call_method"}:
                    raise SpecViolationError(
                        f"call_module is not valid: got a class '{node.target}' ",
                    )

                elif node.op == "call_function":
                    _check_val(node)

                    _check_valid_op(node.target)

                elif node.op == "get_attr":
                    if not isinstance(node.target, str):
                        raise SpecViolationError(
                            f"Expected get_attr target to be string, but got {type(node.target)}"
                        )

                    attr = getattr_recursive(mod, node.target)
                    if isinstance(attr, torch.nn.Module):

                        def _is_type(name, ty):
                            return isinstance(getattr(attr, name, None), ty)

                        if type(attr).__name__ == "LoweredBackendModule":
                            if (
                                _is_type("backend_id", str)
                                and hasattr(attr, "original_module")
                                and hasattr(attr, "module_name")
                                and getattr(attr, "backend_id", None) == "aoti"
                            ):
                                continue
                            if (
                                _is_type("backend_id", str)
                                and _is_type("processed_bytes", bytes)
                                and _is_type("compile_specs", list)
                                and hasattr(attr, "original_module")
                            ):
                                continue
                            else:
                                backend_id = getattr(attr, "backend_id", None)
                                processed_bytes = getattr(attr, "processed_bytes", None)
                                compile_specs = getattr(attr, "compile_specs", None)
                                raise SpecViolationError(
                                    f"Invalid get_attr type {type(attr)}. \n"
                                    f"LoweredBackendModule fields: "
                                    f"backend_id(str) : {type(backend_id)}, "
                                    f"processed_bytes(bytes) : {type(processed_bytes)}, "
                                    f"compile_specs(list) : {type(compile_specs)}"
                                )
                        elif type(attr).__name__ == "AOTInductorEPModule":
                            continue

                        elif type(attr).__name__ == "AOTInductorRunnerWrapper":
                            continue

                    if not isinstance(attr, _allowed_getattr_types(is_toplevel_gm)):
                        raise SpecViolationError(
                            f"Invalid get_attr type {type(attr)} on target {node.target}. \n"
                            f"Valid get_attr types: {_allowed_getattr_types(is_toplevel_gm)}"
                        )

                elif node.op == "placeholder":
                    _check_val(node)
                # TODO(zhxchen17)
                # elif node.op == "output":
                #     _check_flattened_outputs()

        self.check_additional(gm)