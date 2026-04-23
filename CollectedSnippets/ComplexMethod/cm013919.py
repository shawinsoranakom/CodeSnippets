def inner(*args: Any, **kwargs: Any) -> torch.fx.GraphModule:
        # This sets the is_exporting flag when building guards.
        with _compiling_state_context():
            flat_inputs, in_spec = pytree.tree_flatten((args, kwargs))
            check_user_input_output(flat_inputs, UserErrorType.INVALID_INPUT)
            module_to_trace = ModuleToTrace(mod, in_spec)
            orig_callable = mod.forward if isinstance(mod, torch.nn.Module) else mod

            constraints: list[Constraint] | None = _constraints
            dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None = (
                _dynamic_shapes
            )

            from . import reset  # type: ignore[attr-defined]

            reset()

            dynamo_config_ctx = torch._dynamo.config.patch(
                specialize_int=True,
                specialize_float=True,
                assume_static_by_default=True,
                automatic_dynamic_shapes=False,
                capture_dynamic_output_shape_ops=True,
                capture_scalar_outputs=True,
                constant_fold_autograd_profiler_enabled=True,
                log_graph_in_out_metadata=True,
                # install_free_tensors ensures that params and buffers are still
                # added as graph attributes, and makes Dynamo emits graphs that
                # follow export pytree-able input requirements In future, if we
                # fully rely on bytecode for the runtime, we can turn this flag
                # off.
                install_free_tensors=torch._dynamo.config.install_free_tensors_for_export,
            )

            with (
                get_metrics_context(),
                dynamo_timed("fullgraph_capture"),
                dynamo_config_ctx,
            ):
                out = fullgraph_capture(
                    module_to_trace,
                    tuple(flat_inputs),
                    constraints=_constraints,
                    _is_export_deprecated_do_not_use=True,
                )

                assert out.graph_capture_output.output_graph is not None

                example_inputs: list[Any] = []
                if out.backend_input is not None:
                    graph = out.backend_input.graph_module
                    fake_mode = out.backend_input.fake_mode
                    example_inputs = out.backend_input.example_inputs
                else:
                    graph = torch.fx.GraphModule(torch.nn.Module(), torch.fx.Graph())
                    graph.graph.output(None)
                    graph.recompile()
                    fake_mode = None

                _suggest_or_raise_constraint_violation(
                    module_to_trace,
                    orig_callable,
                    fake_mode,
                    out,
                    args,
                    kwargs,
                    dynamic_shapes,
                )

                # Extract export metadata from the new location
                export_metadata = out.graph_capture_output.output_graph.export_metadata
                graph_inputs = export_metadata.graph_input_idx_to_local_source
                graph_output_map = export_metadata.output_return_type
                out_spec = export_metadata.out_spec
                module_call_spec = export_metadata.module_call_spec

            # Compute dynamic dimensions for each input based on constraints
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
                for x in flat_inputs
            ]

            # Create input order mapping from dynamo's internal order to user order
            # Only process inputs that come from function arguments (GetItemSource).
            # Skip inputs that come from other sources like closures (e.g., captured
            # opaque objects like DeviceMesh).
            graph_input_order: dict[int, int] = {}
            for inp in graph_inputs:
                source = graph_inputs[inp]
                if isinstance(source, torch._dynamo.source.GetItemSource):
                    graph_input_order[source.index] = len(graph_input_order)

            for real_idx, graph_idx in graph_input_order.items():
                flat_inputs[real_idx] = example_inputs[graph_idx]

            # Use FX transformer to rebuild the graph cleanly
            transformed_graph = DynamoGraphTransformer(
                graph,
                flat_inputs,
                flat_args_dynamic_dims,
                graph_input_order,
                graph_output_map,
                fake_mode,
                graph_inputs,
            ).transform()

            # Set up PyTree codegen for proper input/output handling
            transformed_graph.graph._codegen = _PyTreeCodeGen(
                _PyTreeInfo(
                    argument_names(inspect.signature(orig_callable), args, kwargs),  # type: ignore[attr-defined, arg-type]
                    in_spec,
                    out_spec,
                )
            )
            transformed_graph.recompile()

            clean_nn_module_stack_and_source_fn(transformed_graph, True)
            clean_export_root(transformed_graph)

            transformed_graph.meta["module_call_specs"] = module_call_spec
            transformed_graph.meta["fake_mode"] = fake_mode

            return transformed_graph