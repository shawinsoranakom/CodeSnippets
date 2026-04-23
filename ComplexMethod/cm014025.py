def _call_user_compiler(
        self, gm: fx.GraphModule, example_inputs: list[Tensor]
    ) -> CompiledFn:
        assert self.compiler_fn is not None
        tot = 0
        placeholders = []
        for node in gm.graph.nodes:
            if node.op in ("call_function", "call_method", "call_module"):
                tot += 1
            if node.op == "placeholder":
                placeholders.append(node)
        increment_op_count(tot)
        for pl in placeholders:
            if not hasattr(pl, "_dynamo_source"):
                arg = pl.meta["grapharg"]
                # TODO: Why isn't this stored in meta :think:
                # NOTE: can't move these into meta: https://github.com/pytorch/pytorch/issues/141640
                pl._dynamo_source = arg.source

        # NOTE: can't move these into meta: https://github.com/pytorch/pytorch/issues/141640
        gm._param_name_to_source = self.param_name_to_source  # type: ignore[assignment]
        gm._source_to_user_stacks = self.source_to_user_stacks  # type: ignore[assignment]

        # Check for per-graph backend override (for debugging/bisecting)
        compiler_fn = (
            get_backend_override_for_compile_id(
                self.dynamo_compile_id, config.debug_backend_override
            )
            or self.compiler_fn
        )

        # Check for per-graph inductor config override (for debugging/bisecting)
        inductor_config_override = get_inductor_config_override_for_compile_id(
            self.dynamo_compile_id, config.debug_inductor_config_override
        )
        if inductor_config_override:
            compiler_fn = _wrap_with_inductor_config(
                compiler_fn, inductor_config_override
            )

        name = (
            compiler_fn.__name__
            if hasattr(compiler_fn, "__name__")
            else "<unknown compiler_fn>"
        )
        from torch._higher_order_ops.passes.inline_invoke_subgraph import (
            inline_invoke_subgraph,
            inline_single_use_invoke_subgraph,
        )

        if config.inline_invoke_subgraph:
            gm = inline_invoke_subgraph(gm)
        elif config.inline_single_use_invoke_subgraph:
            gm = inline_single_use_invoke_subgraph(gm)

        try:
            _step_logger()(logging.INFO, f"calling compiler function {name}")
            if config.verify_correctness:
                compiler_fn = WrapperBackend(compiler_fn)
            compiled_fn = compiler_fn(gm, example_inputs)
            _step_logger()(logging.INFO, f"done compiler function {name}")
            assert callable(compiled_fn), "compiler_fn did not return callable"
        except (TensorifyScalarRestartAnalysis, ShortenTraceback):
            raise
        except exceptions_allowed_to_be_fallback as e:
            if self.has_user_defined_allowed_in_graph:
                raise BackendCompilerFailed(
                    self.compiler_fn, e, inspect.currentframe()
                ).with_traceback(e.__traceback__) from None
            unimplemented_with_warning(
                e,
                self.root_tx.f_code,
                gb_type="Backend compiler exception",
                context=f"Backend: {name}\nException:{str(e)}\nTraceback:\n{self.root_tx.format_frame_summary()}",
                explanation=f"Backend compiler `{name}` failed with {str(e)}. Adding a graph break.",
                hints=[
                    "Report an issue to the backend compiler repo.",
                ],
            )
        except SkipFrame:
            # The backend compiler has requested that we skip the frame, instead of
            # aborting execution.
            raise
        except Exception as e:
            raise BackendCompilerFailed(
                self.compiler_fn, e, inspect.currentframe()
            ).with_traceback(e.__traceback__) from None

        signpost_event(
            "dynamo",
            "OutputGraph.call_user_compiler",
            {
                **self.co_fields,
                "op_count": tot,
                "node_count": len(gm.graph.nodes),
                "input_count": len(placeholders),
            },
        )

        # pyrefly: ignore [bad-return]
        return compiled_fn