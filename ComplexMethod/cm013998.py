def inner(*args: Any, **kwargs: Any) -> ExportResult:
        if not _constraints:
            combined_args = _combine_args(_f, args, kwargs)
            constraints = _process_dynamic_shapes(combined_args, dynamic_shapes)
        else:
            constraints = _constraints

        f = _f
        specialize_float = _specialize_float
        assume_static_by_default = _assume_static_by_default
        check_if_dynamo_supported()
        torch._C._log_api_usage_once("torch._dynamo.export")
        if decomposition_table is not None:
            assert aten_graph, (
                "Specifying a decomposition_table table or tracing mode is illegal without setting aten_graph=True"
            )
        if pre_dispatch:
            assert aten_graph, "pre_dispatch=True can only be used when aten_graph=True"
        f = innermost_fn(f)
        call_to_inspect = f.forward if isinstance(f, torch.nn.Module) else f
        original_signature = inspect.signature(call_to_inspect)  # type: ignore[arg-type]
        graph = None
        out_guards = None
        graph_captured_input = None
        graph_captured_result: tuple[torch.Tensor, ...] | None = None
        fake_mode = None
        result_traced = None

        def guard_export_print(guards: _guards.GuardsSet) -> None:
            nonlocal out_guards
            assert out_guards is None, (
                "whole graph export entails exactly one guard export"
            )
            out_guards = guards

        example_inputs: list[Any] = []

        def dynamo_normalization_capturing_compiler(
            gm: torch.fx.GraphModule, inner_example_inputs: list[Any]
        ) -> Callable[..., Any]:
            nonlocal graph
            assert graph is None, (
                "Tried to emit a second graph during export. Tracing through 'f' must produce a single graph."
            )
            graph = gm

            nonlocal fake_mode, example_inputs
            # NB: do NOT pass inner_example_inputs here, we are detecting the
            # Dynamo allocated fake mode, which should be DISTINCT from a
            # potential outer ambient fake mode which the user provided.
            # example_inputs is always the user specified inputs, so they
            # would have the wrong fake mode attached to them
            fake_mode = _guards.detect_fake_mode()
            example_inputs = inner_example_inputs

            def result_capturing_wrapper(*graph_inputs: Any) -> Any:
                nonlocal graph_captured_result
                nonlocal graph_captured_input

                graph_captured_input = graph_inputs
                assert graph is not None

                named_parameters = dict(graph.named_parameters(remove_duplicate=False))
                named_buffers = dict(graph.named_buffers(remove_duplicate=False))

                ambient_fake_mode = (
                    _guards.detect_fake_mode(graph_inputs)
                    if _guards.detect_fake_mode(graph_inputs) is not None
                    else fake_mode
                )

                # We reran fake tensor propagation, but we didn't do
                # anything with the resulting unbacked SymInts.  Drop them
                # from the pending list.
                # NB: this is wrong if graph_captured_result has
                # data-dependent output size!
                ignore_fresh_unbacked = null_context()
                assert ambient_fake_mode is not None
                if shape_env := ambient_fake_mode.shape_env:
                    ignore_fresh_unbacked = shape_env.ignore_fresh_unbacked_symbols()  # type: ignore[assignment]

                with (
                    ambient_fake_mode,
                    enable_python_dispatcher(),
                    ignore_fresh_unbacked,
                ):
                    params_and_buffers = {
                        **named_parameters,
                        **named_buffers,
                    }
                    fake_params_buffers = {}

                    for name, value in params_and_buffers.items():
                        fake_params_buffers[name] = ambient_fake_mode.from_tensor(
                            value, static_shapes=True
                        )

                    from torch._export.non_strict_utils import (
                        key_path_to_source,
                        KeyPath,
                    )

                    def fakify_with_ambient(
                        path: KeyPath, t: torch.Tensor | _IntWrapper | Any
                    ) -> Any:
                        if isinstance(t, torch.Tensor):
                            # pyrefly: ignore [missing-attribute]
                            return ambient_fake_mode.from_tensor(t, static_shapes=True)
                        elif isinstance(t, _IntWrapper):
                            if (
                                t.dynamism is not None
                                and isinstance(t.dynamism, _DimHint)
                                and t.dynamism.type
                                in (
                                    _DimHintType.DYNAMIC,
                                    _DimHintType.AUTO,
                                )
                            ):  # type: ignore[union-attr]
                                source = key_path_to_source(path)
                                symint = ambient_fake_mode.shape_env.create_unspecified_symint_and_symbol(  # type: ignore[union-attr]
                                    t.val, source, DimDynamic.DYNAMIC
                                )
                                return symint
                            else:
                                return t.val
                        else:
                            return t

                    fake_graph_inputs = pytree.tree_map_with_path(
                        fakify_with_ambient, graph_inputs
                    )
                    graph_captured_result = torch.func.functional_call(
                        graph,
                        fake_params_buffers,  # type: ignore[arg-type]
                        fake_graph_inputs,  # type: ignore[arg-type]
                    )

                return graph_captured_result

            return result_capturing_wrapper

        # Note: This is needed by rewrite_signature. We need to put it before
        # optimize_assert since user program may mutate the inputs.
        flat_args, in_spec = pytree.tree_flatten((args, kwargs))

        remove_from_cache(f)
        constraint_violation_error = None
        if tracing_mode != "symbolic":
            assume_static_by_default = True
        with (
            config.patch(
                specialize_int=True,
                specialize_float=specialize_float,
                assume_static_by_default=assume_static_by_default,
                automatic_dynamic_shapes=False,
                capture_dynamic_output_shape_ops=True,
                capture_scalar_outputs=True,
                constant_fold_autograd_profiler_enabled=True,
                prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
                # install_free_tensors ensures that params and buffers are still
                # added as graph attributes, and makes Dynamo emits graphs that
                # follow export pytree-able input requirements
                install_free_tensors=config.install_free_tensors_for_export,
            ),
            _compiling_state_context(),
        ):
            opt_f = optimize_assert(
                dynamo_normalization_capturing_compiler,
                hooks=Hooks(
                    guard_export_fn=guard_export_print,
                    guard_fail_fn=None,
                ),
                export=True,
                export_constraints=constraints,
            )(f)
            # TODO(voz): We may have instances of `f` that mutate inputs, we should track sideeffects and reject.
            try:
                result_traced = opt_f(*args, **kwargs)
            except ConstraintViolationError as e:
                constraint_violation_error = e
        remove_from_cache(f)

        if (
            not disable_constraint_solver
            and (shape_env := getattr(fake_mode, "shape_env", None)) is not None
            and (dim_constraints := shape_env.dim_constraints) is not None
            and not isinstance(
                call_to_inspect, (torch._ops.OpOverloadPacket, torch._ops.OpOverload)
            )
            and not trace_rules.check(call_to_inspect)
        ):
            dim_constraints.solve()

            forced_specializations = dim_constraints.forced_specializations()

            msg = dim_constraints.prettify_results(
                original_signature,
                dynamic_shapes,
                constraint_violation_error,
                forced_specializations,
            )
            if constraint_violation_error:
                constraint_violation_error.args = (
                    constraint_violation_error.args[0] + msg,
                )
            else:
                if forced_specializations:
                    constraint_violation_error = ConstraintViolationError(msg)
                else:
                    log.info(
                        "Summary of dimension constraints:%s",
                        msg,
                    )

            # Error if we have any constraints on static values

            for k in shape_env.var_to_range:
                if isinstance(k, sympy.Integer):
                    constraint_violation_error = ConstraintViolationError(
                        f"{''.join(traceback.format_list(shape_env.var_to_stack[k]))}\n"
                        "It appears that you're trying to set a constraint on a "
                        f"value which we evaluated to have a static value of {k}. "
                        'Set TORCH_LOGS="+export" for more information.'
                    )
        if constraint_violation_error:
            raise constraint_violation_error

        if graph is None:
            assert same_signature, (
                "Failed to produce a graph during tracing as no tensor operations were found and same_signature is False."
            )
            # If the module does not contain any tensor computation, we would create a graph with inputs and outputs.
            # To be consistent with the graph traced by dynano, `graph` will have only tensor inputs as placeholders
            # and tensor outputs as output nodes. non-tensor inputs and outputs will be added when rewriting signature.
            # We will also construct the `example_inputs`, `graph_captured_input`, and `graph_captured_result` corresponding
            # to `graph`.
            example_inputs = []
            graph_captured_input = ()
            graph_captured_result = ()
            fake_mode = torch._subclasses.FakeTensorMode(
                shape_env=ShapeEnv(), export=True
            )
            if out_guards is None:
                out_guards = _guards.GuardsSet()
            assert out_guards is not None  # suppress mypy error
            parameter_names = list(original_signature.parameters.keys())
            fx_graph = torch.fx.Graph()
            for i, name in enumerate(parameter_names):
                if torch.is_tensor(flat_args[i]):
                    node = fx_graph.placeholder(name)
                    node.meta["val"] = fake_mode.from_tensor(
                        flat_args[i], static_shapes=True
                    )
                    graph_captured_input = graph_captured_input + (flat_args[i],)
                    example_inputs.append(flat_args[i])
            fx_graph.output(graph_captured_result)
            module = torch.nn.Module()
            graph = torch.fx.GraphModule(module, fx_graph)
            log.info(
                "Failed to capture a graph during tracing as no tensor operations were found.:\n\n%s",
                graph.print_readable(print_output=False, colored=True),
            )
        else:
            assert out_guards is not None, "Failed to produce guards during tracing"
            assert fake_mode is not None

            log.info(
                "Dynamo captured graph:\n\n%s",
                graph.print_readable(print_output=False, colored=True),
            )

            # This check need to happened before aten_graph
            # because placeholder's _source_node attribute is not preserved by make_fx
            if same_signature:
                check_signature_rewritable(graph)

        # NB: This is mostly hitting the cache; Dynamo already converted these
        example_fake_inputs = [
            fake_mode.from_tensor(t) if isinstance(t, torch.Tensor) else t
            for t in example_inputs
        ]

        if aten_graph:
            # Running graph with interpreter is needed for propagating the stack_trace
            def graph_with_interpreter(*args: Any) -> Any:
                with torch.fx.traceback.preserve_node_meta():
                    return torch.fx.Interpreter(graph).run(*args)  # type: ignore[arg-type]

            with unset_fake_temporarily(), enable_python_dispatcher(), fake_mode:
                try:
                    graph = make_fx(
                        graph_with_interpreter,
                        decomposition_table=decomposition_table,
                        tracing_mode="real",
                        _allow_non_fake_inputs=True,
                        pre_dispatch=pre_dispatch,
                        _allow_fake_constant=False,
                    )(*example_fake_inputs)
                except CondOpArgsMismatchError as e:
                    # Wrap the internal error to the user-facing error
                    raise UserError(  # noqa: B904
                        UserErrorType.DYNAMIC_CONTROL_FLOW,
                        str(e),
                        case_name="cond_operands",
                    )

            assert graph is not None
            for node in graph.graph.find_nodes(op="get_attr"):
                if isinstance(getattr(graph, node.target), torch.Tensor):  # type: ignore[arg-type]
                    node.meta["val"] = fake_mode.from_tensor(
                        getattr(graph, node.target),  # type: ignore[arg-type]
                        static_shapes=True,
                    )

        if same_signature:
            flat_args_dynamic_dims = [
                {
                    c.dim
                    for c in (constraints or ())
                    if (
                        c.t_id == id(x)
                        and not isinstance(c, _RelaxedConstraint)
                        and c.constraint_range.vr.lower != c.constraint_range.vr.upper
                    )
                }
                for x in flat_args
            ]
            graph = rewrite_signature(
                original_signature,
                graph,
                fake_mode,
                flat_args,
                in_spec,
                example_fake_inputs,
                graph_captured_input,  # type: ignore[arg-type]
                graph_captured_result,
                result_traced,  # type: ignore[possibly-undefined]
                flat_args_dynamic_dims,
            )
        return ExportResult(graph, out_guards)